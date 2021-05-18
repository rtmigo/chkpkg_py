# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT
import os
import sys
from pathlib import Path
from subprocess import run as run_process, CalledProcessError, PIPE, STDOUT, \
    CompletedProcess
from tempfile import TemporaryDirectory
from typing import Optional, List, Union, Type

from ._cleaner import BuildCleaner
from ._exceptions import TwineCheckFailed, FailedToInstallPackage, \
    CannotInitializeEnvironment, CodeExecutionFailed
from ._venvs import TempVenv


def print_command(cmd: Union[str, List[str]], title: str, at: str):
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


def find_latest_wheel(parent_dir: Path) -> Path:
    """Finds *.whl file with the latest modification time"""
    files = [(f.stat().st_mtime, f) for f in parent_dir.glob('*.whl')]
    if not files:
        raise FileNotFoundError(".whl file not found")
    max_mod_time = max((mt for mt, _ in files))
    max_mod_time_file = next(f for t, f in files if t == max_mod_time)
    return max_mod_time_file


class Runner:
    """Prints the commands to the stdout with the same 'at' comments.
    Runs python commands with the same executable.
    """

    def __init__(self, python_exe, at):
        self.python_exe = python_exe
        self.at = at

    def python(self,
               args: Union[str, List[str]],
               title: str,
               cwd: Union[Path, str] = None,
               exception: Type[BaseException] = None):

        args_list = args.split() if isinstance(args, str) else args
        args_list = [self.python_exe] + args_list
        return self._run(args_list, title, cwd, exception)

    def command(self,
                args: Union[str, List[str]],
                title: str,
                cwd: Union[Path, str] = None,
                exception: Type[BaseException] = None,
                executable: str = None,
                shell: bool = False):
        args_list = args
        return self._run(args_list, title, cwd, exception,
                         executable=executable, shell=shell)

    def _run(self,
             args_list,
             title: str,
             cwd: Union[Path, str] = None,
             exception: Type[BaseException] = None,
             executable: str = None,
             shell: bool = False):

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

        builder.python('-m pip install --upgrade pip',
                       title='Upgrading pip',
                       exception=CannotInitializeEnvironment)
        builder.python('-m pip install --upgrade build',
                       title='Installing build',
                       exception=CannotInitializeEnvironment)

        with TemporaryDirectory() as temp_dist_dir:
            # BUILDING ########################################################

            with BuildCleaner(self.project_source_dir):
                builder.python(
                    ['-m', 'build', '--outdir', temp_dist_dir, '--wheel'],
                    title='Building the .whl',
                    cwd=self.project_source_dir)

            # finding the .whl file we just created
            whl = find_latest_wheel(Path(temp_dist_dir))
            whl = whl.absolute()
            print(f'Latest wheel: {whl}')

            # TWINE CHECK #####################################################

            builder.python('-m pip install --upgrade twine',
                           title='Installing twine',
                           exception=CannotInitializeEnvironment)

            # running twine checks on the new file
            builder.python(['-m', 'twine', 'check',
                            os.path.join(temp_dist_dir, '*'), '--strict'],
                           title='Twine check',
                           exception=TwineCheckFailed)

            # TEST VENV #######################################################

            self.installer_venv = TempVenv()

            self._close_us.append(self.installer_venv)
            installer_python = self.installer_venv.__enter__()
            self._installer = Runner(installer_python, at='installer venv')

            self._installer.python('-m pip install --upgrade pip',
                                   title='Upgrading pip',
                                   exception=CannotInitializeEnvironment)

            self._installer.python(
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

    def run_python_code(self, code: str, rstrip: bool = True) -> str:
        with TemporaryDirectory() as temp_current_dir:
            cp = self._installer.python(
                ['-c', code],
                title="Running Python code (cwd is temp dir)",
                cwd=temp_current_dir,
                exception=CodeExecutionFailed)

            return self._output(cp, rstrip)

    @property
    def _can_run_bash(self):
        return os.path.exists("/bin/bash")

    def _run_bash_code(self, code: str, rstrip: bool = True):

        with TemporaryDirectory() as temp_cwd:
            activate = self.installer_venv.paths.posix_bash_activate
            code = '\n'.join(["#!/bin/bash",
                              "set -e",
                              f'source "{activate}"',
                              code])

            # we need executable='/bin/bash' for Ubuntu 18.04, it will run
            # '/bin/sh' otherwise. For MacOS 10.13 it seems to be optional
            cp = self._installer.command(
                code,
                title="Running Bash code (cwd is temp dir)",
                cwd=temp_cwd,
                executable='/bin/bash',
                shell=True,
                exception=CodeExecutionFailed)

            return self._output(cp, rstrip)

    def _run_cmdexe_code(self, code: str, rstrip: bool = True):
        """Runs command in cmd.exe"""
        with TemporaryDirectory() as temp_cwd:
            activate_bat = self.installer_venv.paths.windows_cmdexe_activate

            # temp file with commands to run
            temp_bat_file = Path(temp_cwd) / "_run_cmdexe_code.bat"
            temp_bat_file.write_text(
                '\n'.join([f"CALL {activate_bat}",
                           code]))

            # todo param /u formats output as unicode?
            cp = self._installer.command(
                ["cmd.exe", "/q", "/c", str(temp_bat_file)],
                title="Running code in cmd.exe (cwd is temp dir)",
                cwd=temp_cwd,
                shell=False,
                exception=CodeExecutionFailed)

            return self._output(cp, rstrip)

    def run_shell_code(self, code: str, rstrip: bool = True) -> str:
        if os.name == 'nt':
            method = self._run_cmdexe_code
        else:
            method = self._run_bash_code
        return method(code, rstrip=rstrip)
