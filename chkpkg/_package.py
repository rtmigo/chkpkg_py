# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT

from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import check_call, CalledProcessError
from typing import Optional, List, Union
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

    def _dist_exists(self):
        return (self.project_source_dir / "dist").exists()

    def _build_exists(self):
        return (self.project_source_dir / "build").exists()

    def _eggs_count(self):
        return sum(1 for _ in self.project_source_dir.glob('*.egg-info'))

    def init(self):
        tv = TempVenv()
        self._close_us.append(tv)
        builder_python = tv.__enter__()

        builder = Runner(builder_python, at='builder venv')

        builder.run('-m pip install --upgrade pip',
                    title='Upgrading pip',
                    exception=CannotInitializeEnvironment)

        dist_existed = self._dist_exists()
        build_existed = self._build_exists()
        eggs_count_existed = self._eggs_count()

        builder.run(
            '-m pip install setuptools wheel twine --force-reinstall',
            title='Installing building requirements',
            exception=CannotInitializeEnvironment)

        # the basic command is 'setup.py sdist bdist_wheel'.
        # But it creates ./build, ./dist and ./*.egg-info in the project
        # directory.
        #
        # To avoid modifying the project dir, we create a temp directory
        # for the build and use a little more complicated command
        #
        with TemporaryDirectory() as temp_build_dir:
            dist_dir = os.path.join(temp_build_dir, "dist")

            cmd = ['setup.py',
                   'egg_info', '--egg-base', temp_build_dir,
                   'sdist', '--dist-dir', dist_dir,  # do we need this?
                   'bdist_wheel', '--dist-dir', dist_dir,
                   'clean', '--all']

            builder.run(cmd,
                        title='Building the .whl',
                        cwd=self.project_source_dir)

            # check we did not create new junk
            assert self._dist_exists() == dist_existed
            assert self._build_exists() == build_existed
            assert self._eggs_count() == eggs_count_existed

            # finding the .whl file we just created
            whl = find_latest_wheel(Path(dist_dir))
            whl = whl.absolute()
            print(f'Latest wheel: {whl}')

            # running twine checks on the new file
            builder.run(['-m', 'twine', 'check',
                         os.path.join(dist_dir, '*'), '--strict'],
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
