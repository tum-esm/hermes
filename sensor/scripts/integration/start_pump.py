import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import hardware_interfaces


config = hardware_interfaces.ConfigInterface.read()
pump = hardware_interfaces.PumpInterface(config)
pump.set_desired_pump_rps(30)
