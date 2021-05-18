import sys
from pathlib import Path
from subprocess import check_call

parent = Path(__file__).parent
tests = parent / "test_projects"


def splitter():
    print('\n' + '\n'.join('/' * 80 for _ in range(3)) + '\n')


check_call([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=parent)
splitter()

check_call([sys.executable, 'test_pkg.py'], cwd=tests/'greeter')
splitter()

check_call([sys.executable, 'test_pkg.py'], cwd=tests/'invalid_metadata')

