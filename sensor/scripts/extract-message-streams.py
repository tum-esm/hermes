import os
import sys
import json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

MESSAGE_FILE_PATH = os.path.join(
    PROJECT_DIR, "data", "delivered-mqtt-messages-2023-01-31.json"
)

# TODO: load messags file and parse with custom types datatypy
# TODO: create a list with only CO2 values
# TODO: create a list with only System values
# TODO: create a list with only Air values
# TODO: Save lists into extracted filed
