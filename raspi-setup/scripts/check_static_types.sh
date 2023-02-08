set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

echo "Checking initialize_root.py"
mypy boot-files/midcost-init-files/initialize_root.py

echo "Checking initialize_pi.py"
mypy boot-files/midcost-init-files/initialize_pi.py

echo "Checking run_node_tests.py"
mypy boot-files/midcost-init-files/run_node_tests.py
