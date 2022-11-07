# TODO: remove missing imports

import queue
import RPi.GPIO as GPIO
import time
import pigpio
from threading import Thread
from src.utils import Constants

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
GPIO.setup(Constants.pump.pin_control_out, GPIO.OUT)
GPIO.setup(Constants.pump.pin_speed_in, GPIO.IN)


rps_measurement_queue: queue.Queue[float] = queue.Queue()
last_rps_measurement_time: float | None = None
rps_measurement_count: int = 0


def pump_speed_measurement_interrupt() -> None:
    """ISR for measurement of pump cycle.
    Every 18 falling edges are one full rotation on the pump.
    """
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


class Pump1410:
    timestamp: float = 0
    time_between_cycle: float = 0
    pump_cycle: float = 0

    def __init__(self) -> None:
        self.pi = pigpio.pi()
        assert (
            self.pi.connected
        ), 'pigpio is not connected, please run "sudo pigpiod -n 127.0.0.1"'

        self.pi.hardware_PWM(
            Constants.pump.pin_control_out,
            Constants.pump.frequency,
            0,
        )

        GPIO.add_event_detect(
            Constants.pump.pin_speed_in,
            GPIO.FALLING,
            callback=pump_speed_measurement_interrupt,
        )

    @staticmethod
    def pump_control(
        speed: float,
        duration: float = 0,
        waiting: float = 0,
        activte_speed_correction: bool = True,
    ) -> None:
        """Set speed and runtime of air pump
        speed can be set between 0 and 70 rps
        duration defines the runtime of pump
        waiting defines the waiting time after the pump
        """
        if not Pump1410.pi_initialized:
            Pump1410._init_pump()

        # Hardware limitation is 70 cycle/sec
        assert (
            speed >= 0 and speed <= 100 * 10000 / PUMP_SPEED_TO_DUTY_CYCLE_FACTOR
        ), "Wrong pump speed setting"

        # StateInterface.update({"Pump is running": True})
        data = (
            f"Pump speed {int(speed)}rps, "
            + f"Pump duration {duration}s, "
            + f"Waiting after pump {waiting}s"
        )

        # logger.system_data_logger.info(data)
        print(data)

        Pump1410.pi.hardware_PWM(
            PUMP_SPEED_CONTROL, FREQUENCY, int(speed * PUMP_SPEED_TO_DUTY_CYCLE_FACTOR)
        )
        if activte_speed_correction:
            Pump1410._speed_correction(speed, duration)
        else:
            time.sleep(duration)

        Pump1410.pi.hardware_PWM(PUMP_SPEED_CONTROL, FREQUENCY, 0)
        time.sleep(waiting)

        # StateInterface.update({"Pump is running": False, "Start measurement": True})

    @staticmethod
    def _speed_correction(
        correct_speed: float,
        duration: float,
        kp: float = 0.3,
        ki: float = 0.01,
        kd: float = 0,
    ) -> None:
        """controller to correct the speed to the entered speed
        possible is a PID-Controller
        kp is the P-Controller factor
        ki is the I-Controller factor
        kd is the D-Controller factor
        """
        sum_err: float = 0
        last_err: float = 0
        last_time_between_cycle: float = 0
        duration = time.perf_counter() + duration

        while time.perf_counter() < duration:
            if Pump1410.time_between_cycle <= 0:
                Pump1410.time_between_cycle = 1

            input_speed = (
                Pump1410.pi.get_PWM_dutycycle(PUMP_SPEED_CONTROL)
                / PUMP_SPEED_TO_DUTY_CYCLE_FACTOR
            )
            current_speed = 1 / Pump1410.time_between_cycle
            current_err = correct_speed - current_speed
            # if time doesn't change the pump is not connected or off or the sampling to fast
            if Pump1410.time_between_cycle == last_time_between_cycle:
                current_speed = 0
                current_err = 0

            sum_err += current_err
            diff_err = (current_err - last_err) / Pump1410.time_between_cycle

            new_speed = input_speed + current_err * kp + ki * sum_err + kd * diff_err
            new_duty_cycle = int(new_speed * PUMP_SPEED_TO_DUTY_CYCLE_FACTOR)

            # Limit to max pump settings
            if new_duty_cycle >= 1000000:
                new_duty_cycle = 1000000
            if new_duty_cycle <= 0 or correct_speed == 0:
                new_duty_cycle = 0

            Pump1410.pi.hardware_PWM(PUMP_SPEED_CONTROL, FREQUENCY, new_duty_cycle)
            # print("Input", input_speed," Curr Speed", current_speed," Err",round(current_err,4)," New", round(new_duty_cycle/PUMP_SPEED_TO_DUTY_CYCLE_FACTOR, 2))
            # print("P:",kp*current_err," I:", ki*sum_err," D:", kd*diff_err)
            # print("Current Speed:", current_speed)

            last_err = current_err
            last_time_between_cycle = Pump1410.time_between_cycle
            time.sleep(0.05)

    @staticmethod
    def start_pump(
        speed: float,
        duration: float = 0,
        waiting: float = 0,
        activte_speed_correction: bool = True,
    ) -> None:
        """
        New thread for the pump control
            * kp is the P-Controller factor
            * ki is the I-Controller factor
            * kd is the D-Controller factor
        """
        Pump_control_start = Thread(
            target=Pump1410.pump_control,
            args=(
                speed,
                duration,
                waiting,
                activte_speed_correction,
            ),
        )  # creating a thread
        Pump_control_start.setDaemon(True)  # change Pump_speed_control to daemon
        Pump_control_start.start()  # starting of Thread Pump_speed_control

    @staticmethod
    def end_pump_connection() -> None:
        """
        Set the pump in a save state. Required to end the
        Hardware connection.
        """
        if Pump1410.pi.connected:
            Pump1410.pi.set_PWM_dutycycle(PUMP_SPEED_CONTROL, 0)
            Pump1410.pi.stop()
