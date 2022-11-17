set -o errexit

echo "Checking automation types"
mypy run.py

echo "Checking CLI types"
mypy cli/main.py