from chkpkg import Package, TwineCheckFailed

if __name__ == "__main__":
    try:
        with Package() as pkg:
            pkg.run_python_code('import greeter  # ;)')
        raise AssertionError("Exception not caught")
    except TwineCheckFailed:
        print("\nOK: Caught the exception we expected!")
        exit(0)
