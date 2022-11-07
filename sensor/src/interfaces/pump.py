# TODO: remove missing imports

import queue
import RPi.GPIO as GPIO
import time
import pigpio
from typing import Any
import simple_pid
from src.utils import Constants

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
GPIO.setup(Constants.pump.pin_control_out, GPIO.OUT)
GPIO.setup(Constants.pump.pin_speed_in, GPIO.IN)


rps_measurement_queue: queue.Queue[float] = queue.Queue()
last_rps_measurement_time: float | None = None
rps_measurement_count: int = 0


def _pump_speed_measurement_interrupt(*args: Any) -> None:
    """ISR for measurement of pump cycle.
    Every 18 falling edges are one full rotation on the pump.
    """
    global rps_measurement_count
    global last_rps_measurement_time

    rps_measurement_count += 1
    if rps_measurement_count < 18:
        return
    else:
        rps_measurement_count = 0

    if last_rps_measurement_time is None:
        last_rps_measurement_time = time.perf_counter()
    else:
        cycle_time = time.perf_counter() - last_rps_measurement_time
        last_rps_measurement_time += cycle_time
        rps = 1 / cycle_time
        rps_measurement_queue.put(rps)


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

        self.pid = simple_pid.PID(
            Kp=0.3, Ki=0.01, Kd=0, setpoint=0, output_limits=(0, 100)
        )

    def set_desired_pump_rps(self, rps: float) -> None:
        self.pi.hardware_PWM(
            Constants.pump.pin_control_out,
            Constants.pump.frequency,
            int(rps * Constants.pump.base_rps_factor),
        )

    def get_actual_pump_rps(self) -> float | None:
        rps = 0
        while True:
            try:
                rps = rps_measurement_queue.get_nowait()
            except queue.Empty:
                break
        return rps

    def run(
        self, desired_rps: float, duration: float, speed_correction: float = True
    ) -> None:
        assert 0 <= desired_rps <= 70, "pump hardware limitation is 70 rps"

        start_time = time.time()
        self.set_desired_pump_rps(desired_rps)

        if speed_correction:
            self.pid.setpoint = desired_rps
            while True:
                time.sleep(0.05)
                actual_rps = self.get_actual_pump_rps()
                print(actual_rps)
                if actual_rps is not None:
                    corrected_input_rps = self.pid(actual_rps)
                    if corrected_input_rps is not None:
                        self.set_desired_pump_rps(corrected_input_rps)

                if (time.time() - start_time) > (duration - 0.025):
                    break
        else:
            time.sleep(duration)

        self.set_desired_pump_rps(0)
        self.pid.setpoint = 0

    def teardown(self) -> None:
        """
        Set the pump in a save state. Required to end the
        Hardware connection.
        """
        self.pi.set_PWM_dutycycle(Constants.pump.pin_control_out, 0)
        self.pi.stop()
