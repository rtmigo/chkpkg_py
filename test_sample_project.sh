#!/bin/bash
set -e && cd "${0%/*}"

# Windows tests are executed only from .github/workflows/ci.yml
# This script allows to run some tests locally from POSIX

initial=$PWD
pip3 install -e .
cd "$initial"/test_projects/greeter && python3 ./test_pkg.py
cd "$initial"/test_projects/invalid_metadata && python3 ./test_pkg.py
