import sys


def say_hi():
    print("hi!")


def say_privet():
    print("привет!")  # russian (non-ASCII test)


def cli_run():
    if len(sys.argv) >= 2:
        if sys.argv[1] == "hi":
            say_hi()
            exit()

    # default help option
    # this option will return 2
    print("get your feet back on the ground")
    exit(2)

