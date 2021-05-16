# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT

from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import check_call, CalledProcessError
from typing import Optional, List, Union
import venv
import os


class TwineCheckFailed(BaseException):
    def __init__(self, e):
        self.inner = e


class FailedToInstallPackage(BaseException):
    def __init__(self, e):
        self.inner = e


class CannotInitializeEnvironment(BaseException):
    def __init__(self, e):
        self.inner = e


class CodeExecutionFailed(BaseException):
    def __init__(self, e):
        self.inner = e


def header(s: str, at: str):
    print('=' * 80)
    if at:
        s += ' @ ' + at
    print(s)
    print('-' * 80)


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


def find_latest_wheel(project_root: Path) -> Optional[Path]:
    files = [(f.stat().st_mtime, f) for f in project_root.glob('dist/*.whl')]
    if not files:
        raise FileNotFoundError(".whl file not found")
    max_mod_time = max((mt for mt, _ in files))
    max_mod_time_file = next(f for t, f in files if t == max_mod_time)
    return max_mod_time_file


class Runner:

    def __init__(self, python, at):
        self.python = python
        self.at = at

    def run(self, args: Union[str, List[str]], title=None, cwd=None,
            exception=None):
        args_list = args.split() if isinstance(args, str) else args
        args_list = [self.python] + args_list
        print_command(cmd=args_list, at=self.at, title=title)
        try:
            check_call(args_list, cwd=cwd)
        except CalledProcessError as e:
            if exception is None:
                raise
            else:
                raise exception(e)


# def _contains_setup(path: Path):
#   return (path / "setup.py").exists()


class Package:

    def __init__(self, project_dir: Path = None):
        self._close_us = list()
        self._installer: Optional[Runner] = None

        if project_dir:
            self.project_source_dir = project_dir.absolute()
        else:
            self.project_source_dir = Path('.').absolute()

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

        builder.run(
            '-m pip install setuptools wheel twine --force-reinstall',
            title='Installing building requirements',
            exception=CannotInitializeEnvironment)

        # building the "dist" directory with .whl file inside
        # creates "build", "dist", "*.egg-info"
        builder.run('setup.py sdist bdist_wheel',
                    title='Building the .whl',
                    cwd=self.project_source_dir)

        whl = find_latest_wheel(self.project_source_dir)
        whl = whl.absolute()
        print(f'Latest wheel: {whl}')

        builder.run('-m twine check ./dist/* --strict',
                    title='Twine check',
                    cwd=self.project_source_dir,
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
