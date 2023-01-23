from datetime import datetime
import math
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
        calibration_time = datetime.utcnow().timestamp()

        # TODO: choose random calibration gas order

        # TODO: for each calibration gas

        # TODO: switch air inlet

        self.hardware_interface.co2_sensor.start_calibration_sampling()

        # TODO: set pump to 0.5 litres per minute
        # TODO: wait 5 minutes
        # TODO: take 20 measurements and average them

        self.hardware_interface.co2_sensor.stop_calibration_sampling()

        # TODO: send new correction values to CO2 sensor

        # FIXME: after all gases, check with the last gas again?

        # TODO: switch air inlet

        # TODO: pump at configurable speed for 5 minutes

        # save last calibration time
        state = utils.StateInterface.read()
        state.last_calibration_time = calibration_time
        utils.StateInterface.write(state)

    def is_due(self) -> bool:
        """returns true when calibration procedure should run now"""

        # load state, kept during configuration procedures
        state = utils.StateInterface.read()

        # if last calibration time is unknown, calibrate now
        # should only happen when the state.json is not copied
        # during the upgrade routine or its interface changes
        if state.last_calibration_time is None:
            return True

        seconds_per_calibration_interval = (
            3600 * self.config.calibration.hours_between_calibrations
        )
        current_utc_timestamp = datetime.utcnow().timestamp()
        last_calibration_due_time = (
            math.floor(current_utc_timestamp / seconds_per_calibration_interval)
            * seconds_per_calibration_interval
        )

        return state.last_calibration_time < last_calibration_due_time
