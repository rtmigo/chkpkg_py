# [chkpkg](https://github.com/rtmigo/chkpkg_py#readme)

Checks a Python package intended to be published on PyPi:

- can we build a `.whl` distribution from it?
- сan we install a package from the newly built `.whl`?
- can we import the installed package into the code?

Thus, we check the correctness of `setup.py` or `setup.cfg`.

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

### Step 1: Build, Verify, Install

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

### Step 2: Import, Run

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

If the package must be installed as a CLI program, this can be tested with 
the `run_shell_code`. This function calls `cmd.exe` on Windows and `bash` 
on other systems.

``` python3
output = pkg.run_shell_code('my_package_cli --version')
assert output[0].isdigit()
```

The current working directory will be a random temporary one. If `my_package_cli` 
can be run, then it really is imported into `PATH` and is available from 
everywhere.

However, such tests are best done on a clean system. Otherwise, it may turn out 
that we are running a command that was in the system before the package was 
installed.



### Step 3: Cleanup

``` python3
pkg.cleanup()
```

The `cleanup` method removes all temporary directories created during building
and testing.

