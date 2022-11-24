# doing regular measurements for a few minutes

"""
1. Check wind sensor direction every x seconds
2. If wind direction has changed, pump according to pipe length
3. Check SHT 21 value every x seconds or on inlet change
4. Apply calibration on SHT 21 value changes
5. Do measurements
"""

# TODO: Should I consider pipe length on inlet switches? yes
# TODO: Should I consider pipe length for inlet delays? no
# TODO: Put 50 meter pipe at every inlet. Still configurable.

# class last_measurement_value = datetime.now()
