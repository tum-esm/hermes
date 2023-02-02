import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

from src import custom_types

MESSAGE_ARCHIVE = os.path.join(PROJECT_DIR, "data", "archive")

lines: list[str] = []
for filename in os.listdir(MESSAGE_ARCHIVE):
    if filename.endswith(".json"):
        with open(os.path.join(MESSAGE_ARCHIVE, filename)) as f:
            lines += f.read().split("\n")

messages: list[custom_types.MQTTMessage] = []

decoding_errors = 0
for line in lines:
    try:
        o = json.loads(line)
        if o["variant"] == "data":
            messages.append(custom_types.MQTTDataMessage(**o))
        elif o["variant"] == "status":
            messages.append(custom_types.MQTTStatusMessage(**o))
        else:
            raise Exception
    except:
        decoding_errors += 1

print(f"decoding_errors = {decoding_errors}")
print(f"len(messages) = {len(messages)}")

# TODO: load messags file and parse with custom types datatypy
# TODO: create a list with only CO2 values
# TODO: create a list with only System values
# TODO: create a list with only Air values
# TODO: Save lists into extracted filed
