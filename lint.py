import subprocess


def lint():
    print("Running mypy...")
    if subprocess.call(['mypy', 'chkpkg',
                        #'--ignore-missing-imports'
                        ]) != 0:
        exit(1)



if __name__ == "__main__":
    lint()
