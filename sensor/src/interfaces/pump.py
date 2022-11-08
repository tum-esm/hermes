# TODO: remove missing imports

import queue
import RPi.GPIO as GPIO
import time
import pigpio
from typing import Any
from src.utils import Constants

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
GPIO.setup(Constants.pump.pin_control_out, GPIO.OUT)
GPIO.setup(Constants.pump.pin_speed_in, GPIO.IN)


rps_measurement_queue: queue.Queue[float] = queue.Queue()


def _pump_speed_measurement_interrupt(*args: Any) -> None:
    rps_measurement_queue.put(1)


class PumpInterface:
    def __init__(self) -> None:
        self.pi = pigpio.pi()
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

    def get_pump_cycle_count(self) -> float | None:
        count = 0
        while True:
            try:
                rps_measurement_queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count / 18

    def run(self, desired_rps: float, duration: float) -> None:
        assert 2 <= desired_rps <= 70, "pump hardware limitation is 70 rps"
        self.get_pump_cycle_count()
        self.set_desired_pump_rps(desired_rps)
        self.corrected_input_rps = desired_rps
        time.sleep(duration)

        average_rps = self.get_pump_cycle_count() / duration
        print(f"desired rps = {desired_rps}, average rps = {average_rps}")

        self.set_desired_pump_rps(0)

    def teardown(self) -> None:
        """
        Set the pump in a save state. Required to end the
        Hardware connection.
        """
        self.pi.set_PWM_dutycycle(Constants.pump.pin_control_out, 0)
        self.pi.stop()
