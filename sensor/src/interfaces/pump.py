import queue
import time
import gpiozero
import gpiozero.pins.pigpio
from src import utils, types
from src.utils import Constants

rps_measurement_queue: queue.Queue[float] = queue.Queue()


class PumpInterface:
    def __init__(self, config: types.Config) -> None:
        self.config = config
        self.logger = utils.Logger(config, "pump")

        self.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory(host="127.0.0.1")
        pi_error_message = 'pigpio is not connected, please run "sudo pigpiod -n 127.0.0.1"'
        assert self.pin_factory.connection is not None, pi_error_message
        assert self.pin_factory.connection.connected, pi_error_message

        self.control_pin = gpiozero.PWMOutputDevice(
            pin=Constants.pump.control_pin_out,
            frequency=Constants.pump.frequency,
            active_high=True,
            initial_value=0,
            pin_factory=self.pin_factory,
        )
        self.speed_pin = gpiozero.DigitalInputDevice(
            pin=Constants.pump.speed_pin_in,
            pin_factory=self.pin_factory,
        )
        self.speed_pin.when_activated = lambda: rps_measurement_queue.put(1)

    def set_desired_pump_rps(self, rps: float) -> None:
        self.control_pin.value = rps / 70

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
            f"duration = {duration}, rps = {desired_rps}, actual "
            + f"average rps = {self.get_pump_cycle_count() / duration}"
        )
        if logger:
            self.logger.info(message)
        else:
            print(message)

        # TODO: log warning when avg rps is differing more than 10% from the desired rps

    def teardown(self) -> None:
        """End all hardware connections"""
        self.control_pin.close()
        self.speed_pin.close()
        self.pin_factory.close()
