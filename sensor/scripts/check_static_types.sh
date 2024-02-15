#!/bin/bash

set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

# *********************************************************
# sensor code

echo "Checking run_automation.py"
mypy run_automation.py

echo "Checking run_pump_cycle.py"
mypy run_pump_cycle.py

# *********************************************************
# other

echo "Checking cli/main.py"
mypy cli/main.py

echo "Checking scripts/"
mypy scripts/

echo "Checking tests/"
mypy tests/
