from typing import Literal
from src import utils, types
from src.utils import Constants

try:
    import RPi.GPIO as GPIO

    GPIO.setup(Constants.valves.pin_1_out, GPIO.OUT)
    GPIO.setup(Constants.valves.pin_2_out, GPIO.OUT)
    GPIO.setup(Constants.valves.pin_3_out, GPIO.OUT)
    GPIO.setup(Constants.valves.pin_4_out, GPIO.OUT)
except (ImportError, RuntimeError):
    pass


class ValveInterface:
    def __init__(self, config: types.Config) -> None:
        self.config = config
        self.logger = utils.Logger(config, "valves")
        self.set_active_input(1)

    def set_active_input(self, no: Literal[1, 2, 3, 4], logger: bool = True) -> None:
        if no == 1:
            valve_signal = [GPIO.LOW, GPIO.LOW, GPIO.LOW, GPIO.LOW]
        if no == 2:
            valve_signal = [GPIO.HIGH, GPIO.HIGH, GPIO.LOW, GPIO.LOW]
        if no == 3:
            valve_signal = [GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW]
        if no == 4:
            valve_signal = [GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.HIGH]

        GPIO.output(Constants.valves.pin_1_out, valve_signal[0])
        GPIO.output(Constants.valves.pin_2_out, valve_signal[1])
        GPIO.output(Constants.valves.pin_3_out, valve_signal[2])
        GPIO.output(Constants.valves.pin_4_out, valve_signal[3])

        message = f"switching to valve {no}"
        if logger:
            self.logger.info(message)
        else:
            print(message)
