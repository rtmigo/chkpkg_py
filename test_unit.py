import subprocess
import sys
from pathlib import Path
from subprocess import check_call

parent = Path(__file__).parent
tests = parent / "test_projects"


def splitter(title: str):
    print()
    print('/' * 80)
    print('\\' * 80)
    print('  ' + title.upper())
    print('\\' * 80)
    print('/' * 80)
    print()


if __name__ == "__main__":
    subprocess.check_call([sys.executable, '-m', 'unittest'])
    #exit(0)

    splitter("INSTALLING ITSELF")
    check_call([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=parent)

    splitter("TEST 2")
    check_call([sys.executable, 'test_pkg.py'], cwd=tests / 'greeter')

    splitter("TEST 3")
    check_call([sys.executable, 'test_pkg.py'], cwd=tests / 'invalid_metadata')

    splitter("require pytyped: ok")
    check_call([sys.executable, 'test_pkg.py'],
               cwd=tests / 'greeter_pytyped_ok')

    splitter("require pytyped: fail")
    check_call([sys.executable, 'test_pkg.py'], cwd=tests / 'greeter_pytyped_fail')