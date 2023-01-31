import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import utils, hardware


config = utils.ConfigInterface.read()
pump = hardware.PumpInterface(config)
pump.teardown()
