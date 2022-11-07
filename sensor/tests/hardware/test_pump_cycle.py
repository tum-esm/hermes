import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src.interfaces import PumpInterface


pump = PumpInterface()

for rps in range(10, 71, 10):
    print(f"setting rps to {rps}")
    pump.run(desired_rps=rps, duration=15, speed_correction=True)
    time.sleep(2)

pump.teardown()
