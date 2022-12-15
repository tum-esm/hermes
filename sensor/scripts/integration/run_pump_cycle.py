import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import hardware_interfaces


config = hardware_interfaces.ConfigInterface.read()
pump = hardware_interfaces.PumpInterface(config)

for rps in range(10, 71, 10):
    print(f"setting rps to {rps}")
    pump.run(desired_rps=rps, duration=5, logger=False)
    time.sleep(1)
