import sys
from pathlib import Path
from subprocess import check_call

parent = Path(__file__).parent
tsts = parent / "test_projects"


def divide():
    print('\n' + '\n'.join('/' * 80 for _ in range(3)) + '\n')


check_call([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=parent)
divide()
check_call([sys.executable, 'test_pkg.py'], cwd=tsts / 'greeter')
divide()
check_call([sys.executable, 'test_pkg.py'], cwd=tsts / 'invalid_metadata')
