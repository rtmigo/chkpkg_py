# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import check_call, CalledProcessError
from typing import Optional, List, Union, Iterator
import venv
import os

from ._exceptions import TwineCheckFailed, FailedToInstallPackage, \
    CannotInitializeEnvironment, CodeExecutionFailed


def print_command(cmd, title, at):
    print()
    print('=' * (80 - len(at) - 4) + ' ' + at + ' ==')
    if title is not None:
        print(title)
    print(cmd)
    print('=' * 80)
    print()


def _venv_dir_to_executable(venv_dir: str) -> str:
    p = os.path.join(venv_dir, 'bin', 'python')
    if os.path.exists(p):
        return p
    p = os.path.join(venv_dir, 'Scripts', 'python.exe')
    if os.path.exists(p):
        return p
    raise FileNotFoundError(
        f"Cannot find Python executable inside {venv_dir}")


class TempVenv:
    def __init__(self):
        self._temp_dir: Optional[TemporaryDirectory] = None
        self._executable = None

    @property
    def executable(self):
        if self._executable is None:
            self._executable = _venv_dir_to_executable(self.venv_dir)
            print(f"The python executable: {self._executable}")
        return self._executable

    @property
    def venv_dir(self) -> str:
        return self._temp_dir.name

    def __enter__(self):
        self._temp_dir = TemporaryDirectory()
        assert os.path.exists(self.venv_dir)
        assert os.path.isdir(self.venv_dir)
        print(f"Initializing venv in {self.venv_dir}")
        venv.create(env_dir=self.venv_dir, with_pip=True, clear=True)
        return self.executable

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Removing temp venv dir {self._temp_dir.name}")
        self._temp_dir.cleanup()


def find_latest_wheel(parent_dir: Path) -> Path:
    """Finds *.whl file with the latest modification time"""
    files = [(f.stat().st_mtime, f) for f in parent_dir.glob('*.whl')]
    if not files:
        raise FileNotFoundError(".whl file not found")
    max_mod_time = max((mt for mt, _ in files))
    max_mod_time_file = next(f for t, f in files if t == max_mod_time)
    return max_mod_time_file


class Runner:
    def __init__(self, exe, at):
        self.exe = exe
        self.at = at

    def run(self, args: Union[str, List[str]], title=None, cwd=None,
            exception=None):
        args_list = args.split() if isinstance(args, str) else args
        args_list = [self.exe] + args_list
        print_command(cmd=args_list, at=self.at, title=title)
        try:
            check_call(args_list, cwd=cwd)
        except CalledProcessError as e:
            if exception is None:
                raise
            else:
                raise exception(e)


class BuildCleaner:
    """Removes "dist", "build" and "*.egg-info" directories if the did not
    exist when the object was created."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self._build_existed = self.build_dir.exists()
        self._distr_existed = self.distr_dir.exists()
        self._eggs_existed = list(self.egg_infos)

    @property
    def build_dir(self) -> Path:
        return self.project_dir / "build"

    @property
    def distr_dir(self) -> Path:
        return self.project_dir / "distr"

    @property
    def egg_infos(self) -> Iterator[Path]:
        return self.project_dir.glob('*.egg-info')

    def cleanup(self):

        def remove(p: Path):
            shutil.rmtree(p, ignore_errors=True)

        if not self._build_existed:
            remove(self.build_dir)
        if not self._distr_existed:
            remove(self.distr_dir)

        for egg in self.egg_infos:
            if egg not in self._eggs_existed:
                remove(egg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class Package:
    """During initialization, this object creates a .whl distribution
    and installs the packages from the distribution into a test virtual
    environment.

    After that, using the methods of the object, we can execute commands
    in the test environment, checking that the packages were
    installed correctly."""

    def __init__(self, project_dir: Union[str, Path] = '.'):
        self._close_us = list()
        self._installer: Optional[Runner] = None
        self.project_source_dir = Path(project_dir).absolute()

    def __enter__(self):
        self.init()
        return self

    def init(self):
        tv = TempVenv()
        self._close_us.append(tv)
        builder_python = tv.__enter__()

        builder = Runner(builder_python, at='builder venv')

        builder.run('-m pip install --upgrade pip',
                    title='Upgrading pip',
                    exception=CannotInitializeEnvironment)
        builder.run('-m pip install --upgrade build twine',
                    title='Upgrading build and twine',
                    exception=CannotInitializeEnvironment)

        with TemporaryDirectory() as temp_dist_dir:
            with BuildCleaner(self.project_source_dir):
                builder.run(
                    ['-m', 'build', '--outdir', temp_dist_dir, '--wheel'],
                    title='Building the .whl',
                    cwd=self.project_source_dir)

            # finding the .whl file we just created
            whl = find_latest_wheel(Path(temp_dist_dir))
            whl = whl.absolute()
            print(f'Latest wheel: {whl}')

            # running twine checks on the new file
            builder.run(['-m', 'twine', 'check',
                         os.path.join(temp_dist_dir, '*'), '--strict'],
                        title='Twine check',
                        exception=TwineCheckFailed)

            installer_venv = TempVenv()
            self._close_us.append(installer_venv)
            installer_python = installer_venv.__enter__()
            self._installer = Runner(installer_python, at='installer venv')

            self._installer.run('-m pip install --upgrade pip',
                                title='Upgrading pip',
                                exception=CannotInitializeEnvironment)

            self._installer.run(
                ['-m', 'pip', 'install', '--force-reinstall', str(whl)],
                title=f'Installing {whl.name}',
                exception=FailedToInstallPackage)

    def cleanup(self, exc_type=None, exc_val=None, exc_tb=None):
        for x in reversed(self._close_us):
            x.__exit__(exc_type, exc_val, exc_tb)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup(exc_type, exc_val, exc_tb)

    def run_python_code(self, code: str):
        with TemporaryDirectory() as temp_current_dir:
            self._installer.run(['-c', code],
                                title="Running code (cwd is temp dir)",
                                cwd=temp_current_dir,
                                exception=CodeExecutionFailed)
