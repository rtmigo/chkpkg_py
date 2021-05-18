# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT
import io
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import run as run_process, CalledProcessError, PIPE, STDOUT, \
    CompletedProcess
from typing import Optional, List, Union, Iterator, Type
import venv
import os

from ._exceptions import TwineCheckFailed, FailedToInstallPackage, \
    CannotInitializeEnvironment, CodeExecutionFailed


def print_command(cmd, title, at):
    print()

    print('== ' + title.upper() + ' ' +
          ('=' * (80 - len(at) - len(title) - 4 - 4)) +
          ' ' + at + ' ==')

    if isinstance(cmd, str):
        print(cmd)
    else:
        print(' '.join(repr(arg) for arg in cmd))
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
    def executable(self):
        if self._executable is None:
            self._executable = _venv_dir_to_executable(self.venv_dir)
            print(f"The python executable: {self._executable}")
        return self._executable

    @property
    def venv_dir(self) -> str:
        return self._temp_dir.name

    def create(self):
        self._temp_dir = TemporaryDirectory()
        assert os.path.exists(self.venv_dir)
        assert os.path.isdir(self.venv_dir)
        print(f"Initializing venv in {self.venv_dir}")
        venv.create(env_dir=self.venv_dir, with_pip=True, clear=True)

    def cleanup(self):
        print(f"Removing temp venv dir {self._temp_dir.name}")
        self._temp_dir.cleanup()

    def __enter__(self) -> str:
        self.create()
        return self.executable

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def find_latest_wheel(parent_dir: Path) -> Path:
    """Finds *.whl file with the latest modification time"""
    files = [(f.stat().st_mtime, f) for f in parent_dir.glob('*.whl')]
    if not files:
        raise FileNotFoundError(".whl file not found")
    max_mod_time = max((mt for mt, _ in files))
    max_mod_time_file = next(f for t, f in files if t == max_mod_time)
    return max_mod_time_file


class Runner:
    """Runs commands with the same executable file (until reformat_args=False).
    Prints the commands to the stdout with the same 'at' comments."""

    def __init__(self, exe, at):
        self.exe = exe
        self.at = at

    def run(self,
            args: Union[str, List[str]],
            title: str,
            reformat_args: bool = True,
            cwd: Union[Path, str] = None,
            exception: Type[BaseException] = None,
            executable: str = None,
            shell: bool = False):

        if reformat_args:
            args_list = args.split() if isinstance(args, str) else args
            args_list = [self.exe] + args_list
        else:
            args_list = args

        print_command(cmd=args_list, at=self.at, title=title)

        cp = run_process(args_list, cwd=cwd, encoding=sys.stdout.encoding,
                         stdout=PIPE, stderr=STDOUT,
                         executable=executable,
                         shell=shell,
                         universal_newlines=True)

        output = cp.stdout.rstrip()
        if output:
            print(output)

        if cp.returncode != 0:
            cpe = CalledProcessError(cp.returncode, args_list, cp.stdout,
                                     cp.stderr)
            if exception is None:
                raise cpe
            else:
                raise exception(cpe)

        return cp


class BuildCleaner:
    """Removes "dist", "build" and "*.egg-info" directories if they did not
    exist when the object was created."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.absolute()
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


def run_as_bash_script(script: str, input: bytes = None) -> CompletedProcess:
    """Runs the provided string as a .sh script."""
    # almost same as in VIEN

    # we need executable='/bin/bash' for Ubuntu 18.04, it will run
    # '/bin/sh' otherwise. For MacOS 10.13 it seems to be optional
    return run_process(script, shell=True, executable='/bin/bash',
                       input=input)


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
        self.installer_venv: Optional[TempVenv] = None

    def __enter__(self):
        self.init()
        return self

    def init(self):
        tv = TempVenv()
        self._close_us.append(tv)
        builder_python = tv.__enter__()

        builder = Runner(builder_python, at='builder venv')

        # INSTALLING BUILD ####################################################

        builder.run('-m pip install --upgrade pip',
                    title='Upgrading pip',
                    exception=CannotInitializeEnvironment)
        builder.run('-m pip install --upgrade build',
                    title='Installing build',
                    exception=CannotInitializeEnvironment)

        with TemporaryDirectory() as temp_dist_dir:
            # BUILDING ########################################################

            with BuildCleaner(self.project_source_dir):
                builder.run(
                    ['-m', 'build', '--outdir', temp_dist_dir, '--wheel'],
                    title='Building the .whl',
                    cwd=self.project_source_dir)

            # finding the .whl file we just created
            whl = find_latest_wheel(Path(temp_dist_dir))
            whl = whl.absolute()
            print(f'Latest wheel: {whl}')

            # TWINE CHECK #####################################################

            builder.run('-m pip install --upgrade twine',
                        title='Installing twine',
                        exception=CannotInitializeEnvironment)

            # running twine checks on the new file
            builder.run(['-m', 'twine', 'check',
                         os.path.join(temp_dist_dir, '*'), '--strict'],
                        title='Twine check',
                        exception=TwineCheckFailed)

            # TEST VENV #######################################################

            self.installer_venv = TempVenv()

            self._close_us.append(self.installer_venv)
            installer_python = self.installer_venv.__enter__()
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

    @staticmethod
    def _output(cp: CompletedProcess, rstrip: bool = True) -> str:
        o: str = cp.stdout
        if rstrip:
            o = o.rstrip()
        return o

    def run_python_code(self, code: str, rstrip: bool = True):
        with TemporaryDirectory() as temp_current_dir:
            cp = self._installer.run(['-c', code],
                                     title="Running Python code (cwd is temp dir)",
                                     cwd=temp_current_dir,
                                     exception=CodeExecutionFailed)

            return self._output(cp, rstrip)

    @property
    def _can_run_bash(self):
        return os.path.exists("/bin/bash")

    def _run_bash_code(self, code: str, rstrip: bool = True):
        with TemporaryDirectory() as temp_current_dir:
            activate = os.path.join(self.installer_venv.venv_dir, 'bin',
                                    'activate')

            code = '\n'.join(["#!/bin/bash",
                              "set -e",
                              f'source "{activate}"',
                              code])

            # we need executable='/bin/bash' for Ubuntu 18.04, it will run
            # '/bin/sh' otherwise. For MacOS 10.13 it seems to be optional
            cp = self._installer.run(
                code,
                reformat_args=False,
                title="Running Bash code (cwd is temp dir)",
                cwd=temp_current_dir,
                shell=True, executable='/bin/bash',
                # input=code,
                exception=CodeExecutionFailed)

            return self._output(cp, rstrip)

    def _run_cmdexe_code(self, code: str, rstrip: bool = True):
        """Runs command in cmd.exe"""
        with TemporaryDirectory() as temp_current_dir:
            # file that activates the venv
            activate_bat = os.path.join(
                self.installer_venv.venv_dir,
                'Scripts',
                'activate.bat')
            assert os.path.exists(activate_bat), "activate.bat not found"

            # temp file with commands to run
            temp_bat_file = Path(temp_current_dir) / "_run_cmdexe_code.bat"
            temp_bat_file.write_text(
                '\n'.join([f"CALL {activate_bat}",
                           code]))

            # todo param /u formats output as unicode?
            cp = self._installer.run(
                ["cmd.exe", "/q", "/c", str(temp_bat_file)],
                reformat_args=False,
                title="Running code in cmd.exe (cwd is temp dir)",
                cwd=temp_current_dir,
                shell=True,  # executable='/bin/bash',
                # input=code,
                exception=CodeExecutionFailed)

            return self._output(cp, rstrip)

    def run_shell_code(self, code: str, rstrip: bool = True) -> str:

        if os.name == 'nt':
            method = self._run_cmdexe_code
        else:
            method = self._run_bash_code

        return method(code, rstrip=rstrip)
