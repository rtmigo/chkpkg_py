#!/bin/bash
set -e && source "scripts/pyrel.sh"

pyrel_test_begin  # check we can build the package `greeter`

# check it runs as a command
greeter

# optionally save output to a file to perform some additional checks later
greeter > ~/output.txt

pyrel_test_end  # cleanup