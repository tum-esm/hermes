import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


sensor = interfaces.MainboardSensorInterface()

sensor.log_system_data(logger=False)
