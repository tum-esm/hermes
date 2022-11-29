target_temperature = 40
max_deviation = 0.5

current_temperature: float = sensor.get()

# heating starts below the min threshold
if current_temperature < target_temperature - max_deviation:
    if not heater.is_running():
        heater.start()

# and ends at the target temperature
if current_temperature > target_temperature:
    if heater.is_running():
        heater.stop()

# cooling starts above the max threshold
if current_temperature > target_temperature + max_deviation:
    if not cooling.is_running():
        cooling.start()

# and ends at the target temperature
if current_temperature < target_temperature:
    if cooling.is_running():
        cooling.stop()

"""
on very hot days, the system will swing between 40.0 and 40.5
on other days, the system will swing between 39.5 and 40.0
"""
