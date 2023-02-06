set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

echo "Checking run_automation.py"
mypy run_automation.py

echo "Checking run_headless_enclosure.py"
mypy run_headless_enclosure.py

echo "Checking run_headless_wind_sensor.py"
mypy run_headless_wind_sensor.py

echo "Checking run_pump_cycle.py"
mypy run_pump_cycle.py

echo "Checking cli/main.py"
mypy cli/main.py

echo "Checking scripts/"
mypy scripts/

echo "Checking pytest types"
mypy tests/
