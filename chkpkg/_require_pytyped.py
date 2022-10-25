import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from chkpkg._exceptions import PytypedNotFound


def get_module_path(python_exe: str, module_name: str) -> Path:
    prefix = '<<chkpkg<<'
    suffix = '>>chkpkg>>'

    pycode = \
        f"import sys\n" \
        f"import {module_name}\n" \
        f"print('{prefix}'+sys.modules['{module_name}'].__file__+'{suffix}')\n"

    with TemporaryDirectory() as temp_current_dir:
        # decoding may fail on windows?
        output = subprocess.check_output(
            [python_exe, '-c', pycode],
            encoding=sys.stdout.encoding,
            cwd=temp_current_dir)

    line = next(l for l in output.splitlines()
                if l.startswith(prefix) and l.endswith(suffix))
    name = line[len(prefix):-len(suffix)]

    return Path(name.strip())


def require_dir_contains_pytyped(parent: Path) -> None:
    parent = parent.absolute()
    if not parent.exists():
        raise FileNotFoundError(f"'{parent}' not exists.")
    if not parent.is_dir():
        raise FileNotFoundError(f"'{parent}' is not a directory.")
    pytyped = parent / "py.typed"
    if not pytyped.exists() or not pytyped.is_file():
        raise PytypedNotFound(f'File "{pytyped}" not found')
    print(f"'{pytyped}' exists")
