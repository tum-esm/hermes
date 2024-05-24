#!/bin/bash

set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

# *********************************************************
# sensor code

echo "Checking run_automation.py"
mypy run_automation.py

# *********************************************************
# other

echo "Checking cli/main.py"
mypy cli/main.py

echo "Checking scripts/"
mypy scripts/

echo "Checking tests/"
mypy tests/
