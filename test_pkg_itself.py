# this script tests whether CHKPKG itself is a correct package for PyPi.
# And the tests are done with CHKPKG

from chkpkg import Package

if __name__ == "__main__":
    with Package() as pkg:
        pkg.run_python_code('import chkpkg')

    print("\nPackage is OK!")
