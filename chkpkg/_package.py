# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT

from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import check_call
from typing import Optional, List, Union
import venv
import os


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


class Package:

    def __init__(self):
        self._close_us = list()
        self._installer_python: Optional[str] = None

    def __enter__(self):
        self.init()
        return self

    def init(self):
        tv = TempVenv()
        self._close_us.append(tv)
        builder_python = tv.__enter__()

        def builder_cmd(args: str, title=None):
            cmd = [builder_python] + args.split()
            print_command(cmd=cmd, at='builder venv', title=title)
            check_call(cmd)

        builder_cmd('-m pip install --upgrade pip',
                    title='Upgrading pip')

        builder_cmd(
            '-m pip install setuptools wheel twine --force-reinstall',
            title='Installing building requirements')

        # building the "dist" directory with .whl file inside
        # creates "build", "dist", "*.egg-info"
        builder_cmd('setup.py sdist bdist_wheel', title='Building the .whl')

        project_root = Path('.')
        whl = find_latest_wheel(project_root)
        whl = whl.absolute()
        print(f'Latest wheel: {whl}')

        # running [twine check ./dist/*]
        builder_cmd('-m twine check ./dist/* --strict', title='Twine check')

        installer_venv = TempVenv()
        self._close_us.append(installer_venv)
        self._installer_python = installer_venv.__enter__()

        self._installer_cmd('-m pip install --upgrade pip',
                            title='Upgrading pip')

        self._installer_cmd(
            ['-m', 'pip', 'install', '--force-reinstall', str(whl)],
            title=f'Installing {whl.name}')

    def cleanup(self, exc_type=None, exc_val=None, exc_tb=None):
        for x in reversed(self._close_us):
            x.__exit__(exc_type, exc_val, exc_tb)

    def _installer_cmd(self, s: Union[str, List[str]], title=None, cwd=None):
        args = s.split() if isinstance(s, str) else s
        cmd = [self._installer_python] + args
        print_command(cmd=cmd, at='installer venv', title=title)
        check_call(cmd, cwd=cwd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup(exc_type, exc_val, exc_tb)

    def run_python_code(self, code: str):
        with TemporaryDirectory() as temp_current_dir:
            self._installer_cmd(['-c', code],
                                title="Running code (cwd is temp dir)",
                                cwd=temp_current_dir)
