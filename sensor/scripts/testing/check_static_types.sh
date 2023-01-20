set -o errexit

echo "Checking automation types"
mypy run.py

echo "Checking headless enclosure types"
mypy run_headless_enclosure.py

echo "Checking headless wind sensor types"
mypy run_headless_wind_sensor.py

echo "Checking CLI types"
mypy cli/main.py

echo "Checking pytest types"
mypy tests/
