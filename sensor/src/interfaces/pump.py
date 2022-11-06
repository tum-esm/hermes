# TODO: remove missing imports

import RPi.GPIO as GPIO
import time
import pigpio
from threading import Thread
from src.utils import logger  # , StateInterface


PUMP_SPEED_CONTROL = 19
PUMP_TACHO_INPUT = 16
FREQUENCY = 10000
# The value is the result of a measurement between duty cycle and input speed
PUMP_SPEED_TO_DUTY_CYCLE_FACTOR = 1.344973917 * 10000

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme

GPIO.setup(PUMP_SPEED_CONTROL, GPIO.OUT)
GPIO.setup(PUMP_TACHO_INPUT, GPIO.IN)


class Pump1410:
    timestamp: float = 0
    time_between_cycle: float = 0
    pump_cycle: float = 0

    pi = pigpio.pi()
    pi_initialized = False

    @staticmethod
    def _init_pump() -> None:
        if not Pump1410.pi.connected:
            exit()

        Pump1410.pi.hardware_PWM(PUMP_SPEED_CONTROL, FREQUENCY, 0)  # Initial

        # Interrupt-Event fuer Pumpe hinzufuegen, fallende Flanke
        GPIO.add_event_detect(
            PUMP_TACHO_INPUT, GPIO.FALLING, callback=Pump1410.PUMP_TACHO_INPUT_Interrupt
        )
        Pump1410.pi_initialized = True

    # Callback-Funktion
    @staticmethod
    def PUMP_TACHO_INPUT_Interrupt() -> None:
        """ISR for measurment of pump cycle.
        Every 18 falling edges are one full rotation on the pump.
        The function provides the time between the cycles.
        """
        Pump1410.pump_cycle += 1
        if Pump1410.pump_cycle >= 18:  # 18 peaks are one full rotaion
            Pump1410.time_between_cycle = time.perf_counter() - Pump1410.timestamp
            # print(1/Pump1410.time_between_cycle)
            Pump1410.timestamp = time.perf_counter()
            Pump1410.pump_cycle = 0

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
