from src import custom_types, utils, hardware


class CalibrationProcedure:
    """runs when a calibration is due"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="calibration-procedure"), config
        self.hardware_interface = hardware_interface

    def run(self) -> None:
        pass

        # TODO: implement calibration procedure
