#!/bin/bash

# we will test CHKPKG itself with PYREL, an older package for the same task

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