from chkpkg import Package, PytypedNotFound

if __name__ == "__main__":
    with Package() as pkg:
        caught = False
        try:
            pkg.require_pytyped("greeter")
        except PytypedNotFound:
            caught = True
            print("Caught PytypedNotFound (OK)")

        if not caught:
            raise Exception("Did not catch PytypedNotFound")

    print("\nPackage is OK!")
