#!/bin/bash
set -e && cd "${0%/*}"

pip3 install -e .
cd sample_project

python3 test_pkg.py