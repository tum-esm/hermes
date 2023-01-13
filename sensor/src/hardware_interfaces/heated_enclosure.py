import re

number_regex = r"\d+(\.\d+)?"
measurement_pattern = re.compile(
    f"version: {number_regex}; target: {number_regex}; allowed "
    + f"deviation: {number_regex}; measured: {number_regex};"
)
relais_status_pattern = re.compile(r"heater: (on|off); fan: (on|off)")


class HeatedEnclosureInterface:
    pass
