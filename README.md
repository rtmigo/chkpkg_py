# [chkpkg](https://github.com/rtmigo/chkpkg_py#readme)

Checks a Python package intended to be published on PyPi:

- can we build a `.whl` distribution from it?
- сan we install a package from the newly built `.whl`?
- can we import the installed package into the code?

`chkpkg` can be used as part of CI pipeline. The check can be run from a `.py`
script, which is as cross-platform as Python itself.


---

`chkpkg` was tested in Python 3.6-3.9 on macOS, Ubuntu and Windows.

# Install

``` bash
pip3 install chkpkg
```

# Use

``` python3
from chkpkg import Package

with Package() as pkg:
    pkg.run_python_code('import mypackage; mypackage.myfunc()')
    
print("Package is OK!")
```

This code creates a distribution, installs the package from that distribution,
imports the newly installed package and calls `myfunc()` from it. If at least
one command returned a non-zero exit code, an exception would be thrown. The
absence of exceptions means that the package is fine.

By default, we assume that the `setup.py` or `setup.cfg` is located in the
current working directory. You can specify a different path using the
argument `Package(project_dir=...)`

## Steps

Without context, the code would look like this:

``` python3
from chkpkg import Package

pkg = Package()

try:
    # step 1
    pkg.install()
    
    # step 2   
    pkg.run_python_code('import mymodule')

finally:
    # step 3
    pkg.cleanup()    
```

### Step 1: build, verify, install

``` python3
pkg.install()
```

The `install` method:

- Creates a temporary virtual environment capable of building `.whl` files
    - Creates a distribution as a `.whl` file (`python -m build`)
    - Verifies the package source (`twine check --strict`)
- Creates another temporary virtual environment without preinstalled packages
    - Installs the package from the newly created `.whl` into the clean virtual
      environment

### Step 2: import, run

``` python3
pkg.run_python_code('import my_package')
```

The `run_python_code` method allows you to check that the package is installed
and can be imported without errors.

You can also run some functions from the imported package and check the output.

``` python3
output = pkg.run_python_code('import my_package; print(my_package.sum(2, 3))')
assert output == "5"
```

### Step 3: cleanup

``` python3
pkg.cleanup()
```

The `cleanup` method removes all temporary directories created during building
and testing.

