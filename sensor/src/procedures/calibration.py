from src import custom_types, utils


class CalibrationProcedure:
    """runs when a calibration is due"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(config, origin="calibration")
        self.config = config

    def run(self) -> None:
        pass

        # TODO: implement calibration procedure
