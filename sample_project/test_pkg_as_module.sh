#!/bin/bash
set -e && source "scripts/pyrel.sh"

pyrel_test_begin  # check we can build the package `greeter`

# check we can import it
python3 -c "import greeter"

# optionally save output to a file to perform some additional checks later
python3 -c "import greeter; greeter.say_hi()" > ~/output.txt

pyrel_test_end  # cleanup