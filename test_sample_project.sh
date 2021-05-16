#!/bin/bash
set -e && cd "${0%/*}"

# Windows tests are executed only from .github/workflows/ci.yml
# This script allows to run some tests locally from POSIX

pip3 install -e .


cd "${0%/*}"/test_projects/greeter && python3 ./test_pkg.py
cd "${0%/*}"/test_projects/invalid_metadata && python3 ./test_pkg.py

