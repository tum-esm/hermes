#!/bin/bash

set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

# *********************************************************
# raspi setup

echo "Checking raspi-setup-files/midcost-init-files/initialize_root.py"
mypy raspi-setup-files/midcost-init-files/initialize_root.py

echo "Checking raspi-setup-files/midcost-init-files/initialize_pi.py"
mypy raspi-setup-files/midcost-init-files/initialize_pi.py

echo "Checking raspi-setup-files/midcost-init-files/run_node_tests.py"
mypy raspi-setup-files/midcost-init-files/run_node_tests.py

# *********************************************************
# sensor code

echo "Checking run_automation.py"
mypy run_automation.py

echo "Checking run_headless_enclosure.py"
mypy run_headless_enclosure.py

echo "Checking run_headless_wind_sensor.py"
mypy run_headless_wind_sensor.py

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
