from chkpkg import Package

if __name__ == "__main__":
    with Package() as pkg:
        pkg.require_pytyped("greeter")  # no errors

    print("\nPackage is OK!")
