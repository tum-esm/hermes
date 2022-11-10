import queue
import time
from typing import Any
from src import utils, types
from src.utils import Constants

try:
    import pigpio
    import RPi.GPIO as GPIO

    GPIO.setup(Constants.pump.pin_control_out, GPIO.OUT)
    GPIO.setup(Constants.pump.pin_speed_in, GPIO.IN)
except (ImportError, RuntimeError):
    pass


rps_measurement_queue: queue.Queue[float] = queue.Queue()


def _pump_speed_measurement_interrupt(*args: Any) -> None:
    rps_measurement_queue.put(1)


class PumpInterface:
    def __init__(self, config: types.Config) -> None:
        self.pi = pigpio.pi("127.0.0.1")
        self.config = config
        self.logger = utils.Logger(config, "pump")
        assert (
            self.pi.connected
        ), 'pigpio is not connected, please run "sudo pigpiod -n 127.0.0.1"'

        self.pi.set_PWM_dutycycle(
            Constants.pump.pin_control_out,
            0,
        )
        self.pi.hardware_PWM(
            Constants.pump.pin_control_out,
            Constants.pump.frequency,
            0,
        )
        GPIO.add_event_detect(
            Constants.pump.pin_speed_in,
            GPIO.FALLING,
            callback=_pump_speed_measurement_interrupt,
        )

    def set_desired_pump_rps(self, rps: float) -> None:
        self.pi.hardware_PWM(
            Constants.pump.pin_control_out,
            Constants.pump.frequency,
            int(rps * Constants.pump.base_rps_factor),
        )

    def get_pump_cycle_count(self) -> float:
        count = 0
        while True:
            try:
                rps_measurement_queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count / 18

    def run(self, desired_rps: float, duration: float, logger: float = True) -> None:
        assert 2 <= desired_rps <= 70, "pump hardware limitation is 70 rps"
        self.get_pump_cycle_count()  # empty rps_measurement_queue

        self.set_desired_pump_rps(desired_rps)
        time.sleep(duration)
        self.set_desired_pump_rps(0)

        message = (
            f"duration = {duration}, rps = {desired_rps}, actual"
            + f"average rps = {self.get_pump_cycle_count() / duration}"
        )
        if logger:
            self.logger.info(message)
        else:
            print(message)

        # TODO: log when avg rps is differing more than 5% from the desired rps

    def teardown(self) -> None:
        """
        Set the pump in a save state. Required to end the
        Hardware connection.
        """
        self.pi.set_PWM_dutycycle(Constants.pump.pin_control_out, 0)
        self.pi.stop()
