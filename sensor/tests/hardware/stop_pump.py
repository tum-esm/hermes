import os
import sys
import time

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src.interfaces import PumpInterface


pump = PumpInterface()
pump.set_desired_pump_rps(0)
pump.teardown()
