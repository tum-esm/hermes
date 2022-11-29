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

from src import types, utils


class MeasurementProcedure:
    """runs every mainloop call when no configuration or calibration ran"""

    def __init__(self, config: types.Config) -> None:
        self.logger = utils.Logger(config, origin="measurements")

    def run(self, config: types.Config) -> None:
        self.logger.update_config(config)

        # TODO: implement measurement procedure
