import sys
from pathlib import Path
from subprocess import check_call

parent = Path(__file__).parent
tests = parent / "test_projects"


def splitter(title: str):
    print()
    print('/' * 80)
    print('\\' * 80)
    print('  '+title.upper())
    print('\\' * 80)
    print('/' * 80)
    print()


splitter("POINT 1")
check_call([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=parent)

splitter("TEST 2")
check_call([sys.executable, 'test_pkg.py'], cwd=tests / 'greeter')

splitter("TEST 3")
check_call([sys.executable, 'test_pkg.py'], cwd=tests / 'invalid_metadata')
