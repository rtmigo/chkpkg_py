#!/bin/bash

# this script tests whether CHKPKG itself is a correct package for PyPi.
# The script uses PYREL (another tool for testing packages).
# Sadly, PYREL does not work on Windows, so this check is POSIX-only.
#
# However, the correctness of CHKPKG on Windows is tested indirectly.
# I am using CHKPKG to test other packages. And those tests would not pass
# if CHKPKG was not installed correctly from PyPi.

set -e

wget -O /tmp/pyrel.sh https://raw.githubusercontent.com/rtmigo/pyrel/master/pyrel.sh
source /tmp/pyrel.sh

# build package, install it into virtual
# environment with pip
pyrel_test_begin

# check, that we can import this module by name
# (so it's installed)
python3 -c "import chkpkg"

# remove generated package
pyrel_test_end