import os
import venv
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union, Optional


class VenvPaths:
    def __init__(self, venv_dir: Union[Path, str]):
        self.venv_dir = Path(venv_dir)

    @property
    def executable(self):
        p = self.venv_dir / 'bin' / 'python'
        if p.exists():
            return p
        p = self.venv_dir / 'Scripts' / 'python.exe'
        if p.exists():
            return p
        raise FileNotFoundError(
            f"Cannot find Python executable inside {self.venv_dir}")

    @property
    def windows_cmdexe_activate(self):
        # https://docs.python.org/3/library/venv.html
        p = self.venv_dir / 'Scripts' / 'activate.bat'
        if not p.exists():
            raise FileNotFoundError
        return p

    @property
    def posix_bash_activate(self):
        # https://docs.python.org/3/library/venv.html
        p = self.venv_dir / 'bin' / 'activate'
        if not p.exists():
            raise FileNotFoundError
        return p


class TempVenv:
    """Creates virtual environment in a temporary directory.
    Removes the directory and the environment when `cleanup` is called.
    Can be used as context manager:

    with TempVenv() as python_exe:
        run([python_exe, '-m', 'module'])
    """

    def __init__(self):
        self._temp_dir: Optional[TemporaryDirectory] = None
        self._executable = None

    @property
    def venv_dir_str(self) -> str:
        return self._temp_dir.name

    @property
    def paths(self) -> VenvPaths:
        return VenvPaths(self._temp_dir.name)

    def create(self):
        self._temp_dir = TemporaryDirectory()
        assert os.path.exists(self.venv_dir_str)
        assert os.path.isdir(self.venv_dir_str)
        print(f"Initializing venv in {self.venv_dir_str}")
        venv.create(env_dir=self.venv_dir_str, with_pip=True, clear=True)

    def cleanup(self):
        print(f"Removing temp venv dir {self._temp_dir.name}")
        self._temp_dir.cleanup()

    def __enter__(self) -> str:
        self.create()
        return str(self.paths.executable)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()