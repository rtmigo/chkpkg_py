[![PyPI version shields.io](https://img.shields.io/pypi/v/chkpkg.svg)](https://pypi.python.org/pypi/chkpkg/)
[![Generic badge](https://img.shields.io/badge/Python-3.6+-blue.svg)](#)
[![Generic badge](https://img.shields.io/badge/OS-Windows%20|%20macOS%20|%20Linux-blue.svg)](#)
[![Downloads](https://pepy.tech/badge/chkpkg/month)](https://pepy.tech/project/chkpkg)

# [chkpkg](https://github.com/rtmigo/chkpkg_py#readme)

Checks a Python package intended to be published on PyPi:

- can we build a `.whl` distribution from it?
- сan we install a package from the newly built `.whl`?
- can we import the installed package into the code?

Thus, we test the correctness of `setup.py` or `setup.cfg`.

`chkpkg` can be used as part of CI pipeline. The check can be run from a `.py`
script, which is as cross-platform as Python itself.

---

`chkpkg` supports Python 3.6+ on Linux, macOS and Windows.

# Install

``` bash
pip3 install chkpkg
```

# Use

``` python3
from chkpkg import Package

with Package() as pkg:
    pkg.run_python_code('import mypackage; mypackage.myfunc()')
    pkg.run_shell_code('mypackage_cli --version')
    
print("Package is OK!")
```

This **test script** creates a distribution from project sources, installs the
package from the distribution into a virtual environment, tries importing and
running the installed package from python and command line.

If any results in an error, an exception is thrown. The absence of exceptions
means that the package is fine.

By default, we assume that the `setup.py` or `setup.cfg` is located in the
current working directory. You can specify a different path using the
argument `Package(project_dir=...)`

# Steps

Without context, the test script would look like this:

``` python3
from chkpkg import Package

pkg = Package()

try:
    # step 1
    pkg.init()
    
    # step 2   
    pkg.run_python_code('import mypackage; mypackage.myfunc()')
    pkg.run_shell_code('mypackage_cli --version')

finally:
    # step 3
    pkg.cleanup()    
```

## Step 1: Build, Verify, Install

``` python3
pkg.init()
```

The `init` method:

- Creates a temporary virtual environment capable of building `.whl` files
    - Creates a distribution as a `.whl` file (`python -m build`)
    - Verifies the package source (`twine check --strict`)
- Creates another temporary virtual environment without preinstalled packages
    - Installs the package from the newly created `.whl` into the clean virtual
      environment

## Step 2: Import, Run

``` python3
pkg.run_python_code('import mypackage')
```

The `run_python_code` method allows you to check that the package is installed
and can be imported without errors.

You can also run some functions from the imported package and check the output.

``` python3
output = pkg.run_python_code('import mypackage; print(mypackage.plus(2, 3))')
assert output == "5"
```

If the package must be installed as a CLI program, this can be tested with
the `run_shell_code`. This function calls `cmd.exe` on Windows and `bash`
on other systems.

``` python3
output = pkg.run_shell_code('mypackage_cli --version')
assert output[0].isdigit()
```

The current working directory will be a random temporary one. If `mypackage_cli`
can be run, then it really is available as a shell command from any directory.

However, such tests are best done on a clean system. If we run the tests on
development machine, it may turn out that we are running a command that was in
the system before the package was installed.

## Step 3: Cleanup

``` python3
pkg.cleanup()
```

The `cleanup` method removes all temporary directories created during building
and testing.

# License

Copyright © 2021 [Artёm iG](https://github.com/rtmigo).
Released under the [MIT License](LICENSE).