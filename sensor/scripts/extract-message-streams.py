from datetime import datetime
import json
import os
import sys
import matplotlib.pyplot as plt

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

from src import custom_types
import matplotlib.dates as dates

MESSAGE_ARCHIVE = os.path.join(PROJECT_DIR, "data", "archive")

lines: list[str] = []
for filename in os.listdir(MESSAGE_ARCHIVE):
    if filename.endswith(".json"):
        with open(os.path.join(MESSAGE_ARCHIVE, filename)) as f:
            lines += f.read().split("\n")

data_messages: list[custom_types.MQTTDataMessage] = []
log_messages: list[custom_types.MQTTLogMessage] = []

decoding_errors = 0
for line in lines:
    try:
        o = json.loads(line)
        if o["variant"] == "data":
            data_messages.append(custom_types.MQTTDataMessage(**o))
        elif o["variant"] == "status":
            log_messages.append(custom_types.MQTTLogMessage(**o))
        else:
            raise Exception
    except:
        decoding_errors += 1

print(f"decoding_errors = {decoding_errors}")
print(f"len(data_messages) = {len(data_messages)}")
print(f"len(log_messages) = {len(log_messages)}")


co2_data = [
    (datetime.fromtimestamp(m.body.timestamp), m.body.value)
    for m in data_messages
    if isinstance(m.body.value, custom_types.MQTTCO2Data)
]
air_data = [
    (datetime.fromtimestamp(m.body.timestamp), m.body.value)
    for m in data_messages
    if isinstance(m.body.value, custom_types.MQTTAirData)
]
system_data = [
    (datetime.fromtimestamp(m.body.timestamp), m.body.value)
    for m in data_messages
    if isinstance(m.body.value, custom_types.MQTTSystemData)
]

print(f"len(co2_data) = {len(co2_data)}")
print(f"len(air_data) = {len(air_data)}")
print(f"len(system_data) = {len(system_data)}")


fig, ax = plt.subplots(
    2, 1, gridspec_kw={"height_ratios": [3, 1], "hspace": 0.3}, figsize=(10, 8)
)

top_plot = plt.subplot(2, 1, 1)
top_plot.grid(True)
top_plot.set_title("Raw CO2 concentration")
top_plot.set_xlabel("local time")
top_plot.set_ylabel("concentration [ppm]")

top_plot.scatter(
    [c[0] for c in co2_data],
    [c[1].data.raw for c in co2_data],
    label="raw co2",
    color="red",
    s=0.05,
    alpha=0.5,
)

top_plot.xaxis.set_minor_locator(dates.SecondLocator(interval=4 * 3600))  # every hours
top_plot.xaxis.set_minor_formatter(dates.DateFormatter("%H:%M"))  # hours and minutes
top_plot.xaxis.set_major_locator(dates.DayLocator(interval=1))  # every day
top_plot.xaxis.set_major_formatter(dates.DateFormatter("\n%d-%m-%Y"))

bottom_plot = plt.subplot(2, 1, 2)
bottom_plot.grid(True)
bottom_plot.set_title("Temperature Data")
bottom_plot.set_xlabel("local time")
bottom_plot.set_ylabel("")

bottom_plot.scatter(
    [c[0] for c in air_data],
    [c[1].data.inlet_temperature for c in air_data],
    label="inlet temperature",
    color="red",
    s=0.2,
    alpha=0.75,
)
bottom_plot.scatter(
    [c[0] for c in system_data],
    [c[1].data.cpu_temperature for c in system_data],
    label="cpu temperature",
    color="green",
    s=0.2,
    alpha=0.75,
)
bottom_plot.scatter(
    [c[0] for c in system_data],
    [c[1].data.mainboard_temperature for c in system_data],
    label="mainboard temperature",
    color="blue",
    s=0.2,
    alpha=0.75,
)
bottom_plot.legend()

bottom_plot.xaxis.set_minor_locator(
    dates.SecondLocator(interval=4 * 3600)
)  # every hours
bottom_plot.xaxis.set_minor_formatter(dates.DateFormatter("%H:%M"))  # hours and minutes
bottom_plot.xaxis.set_major_locator(dates.DayLocator(interval=1))  # every day
bottom_plot.xaxis.set_major_formatter(dates.DateFormatter("\n%d-%m-%Y"))

plt.savefig("some.png", dpi=300)

# TODO: create a list with only CO2 values
# TODO: create a list with only System values
# TODO: create a list with only Air values
