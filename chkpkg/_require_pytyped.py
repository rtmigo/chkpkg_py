import subprocess
from pathlib import Path

from chkpkg._exceptions import PytypedNotFound


def get_module_path(python_exe: str, module_name: str) -> Path:
    pycode = f"import sys\n" \
             f"import {module_name}\n" \
             f"print(sys.modules['{module_name}'].__file__)\n"

    # decoding may fail on windows?
    output = subprocess.check_output([python_exe, '-c', pycode]).decode()
    return Path(output.strip())


def require_dir_contains_pytyped(parent: Path) -> None:
    if not parent.is_dir() or not parent.exists():
        raise ValueError(parent)
    pytyped = parent / "py.typed"
    if not pytyped.exists() or not pytyped.is_file():
        raise PytypedNotFound(f'File "{pytyped}" not found')
