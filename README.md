# [chkpkg](https://github.com/rtmigo/chkpkg_py#readme)

Checks a Python package intended to be published on PyPi:

- can we build a `.whl` distribution from it?
- сan we install a package from the newly built `.whl`?
- can we import the installed package into the code?

`chkpkg` can be used as part of CI pipeline. All configuration is done from a
Python script, which is as cross-platform as Python itself.


---

`chkpkg` was tested in Python 3.6, 3.9 and 3.10-beta.1 on macOS, Ubuntu and
Windows.

# Install

``` bash
pip3 install chkpkg
```

# Use

``` python3
from chkpkg import Package

with Package() as pkg:
    pkd.run_python_code('import mymodule')
```

This code runs many commands in child processes. If at least one of them returns
a non-zero exit code, an exception will be thrown.

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

### Step 1: check, build, install

``` python3
pkg.install()
```

The `install` method:

- Creates a temporary virtual environment capable of building `.whl` files
    - Verifies the package source with `twine check`
    - Creates a distribution as a `.whl` file
- Creates another temporary virtual environment without preinstalled packages
    - Installs the package from the newly created `.whl` into the clean virtual
      environment

### Step 2: import, run

``` python3
pkg.run_python_code('import my_package')
```

The `run_python_code` method allows you to check that the package is installed
and can be imported without errors.

You can also run some functions from the imported package.

``` python3
pkg.run_python_code('import my_package; print(my_package.func())')
```

The main question here is whether the code will execute successfully (with exit
code 0) or will an error occur (with non-zero exit codes).

### Step 3: cleanup

``` python3
pkg.cleanup()
```

The `cleanup` method removes all temporary directories created during building
and testing.

