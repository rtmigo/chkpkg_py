#!/bin/bash
set -e && cd "${0%/*}"

# Windows tests are executed only from .github/workflows/ci.yml
# This script allows to run some tests locally from POSIX

pip3 install -e .
cd sample_project

python3 test_pkg.py