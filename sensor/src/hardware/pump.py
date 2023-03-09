import multiprocessing
import queue
import time
from typing import Literal, Optional
import gpiozero
import gpiozero.pins.pigpio
from src import utils, custom_types

PUMP_CONTROL_PIN_OUT = 19
PUMP_CONTROL_PIN_FREQUENCY = 10000
PUMP_SPEED_PIN_IN = 16


class PumpInterface:
    class DeviceFailure(Exception):
        """raised when the pump either reports an rps which is off
        by more than 15% from the desired rps"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger, self.config = utils.Logger("pump"), config
        self.logger.info("Starting initialization")

        # ---------------------------------------------------------------------
        # INITIALIZING THE PUMP CONTROL PIN

        # pin factory required for hardware PWM
        self.pin_factory = utils.get_gpio_pin_factory()

        # pins for setting desired pump speed
        self.control_pin = gpiozero.PWMOutputDevice(
            pin=PUMP_CONTROL_PIN_OUT,
            frequency=PUMP_CONTROL_PIN_FREQUENCY,
            active_high=True,
            initial_value=0,
            pin_factory=self.pin_factory,
        )

        # ---------------------------------------------------------------------
        # LOGGING ACTUAL PUMP CYCLES

        # queues to communicate with rps monitoring process
        self.rps_measurement_queue: queue.Queue[float] = queue.Queue()
        self.desired_rps_queue: queue.Queue[tuple[float, float]] = queue.Queue()
        self.rps_monitoring_exceptions: queue.Queue[str] = queue.Queue()

        # pins for measuring actual pump speed
        self.speed_pin = gpiozero.DigitalInputDevice(
            pin=PUMP_SPEED_PIN_IN,
            pin_factory=self.pin_factory,
        )
        self.speed_pin.when_activated = lambda: self.rps_measurement_queue.put(1)

        # ---------------------------------------------------------------------
        # PUMP RPS MONITORING IN A THREAD

        self.rps_monitoring_process = multiprocessing.Process(
            target=PumpInterface.monitor_rps,
            args=(
                config,
                self.rps_measurement_queue,
                self.desired_rps_queue,
                self.rps_monitoring_exceptions,
            ),
        )
        if self.config.active_components.pump_speed_monitoring:
            self.rps_monitoring_process.start()

        # ---------------------------------------------------------------------

        self.logger.info("Finished initialization")

    def set_desired_pump_speed(
        self,
        unit: Literal["rps", "litres_per_minute"],
        value: float,
    ) -> None:
        """set rps between 0 and 70"""
        rps: float = value
        if unit == "litres_per_minute":
            rps = value / (60 * self.config.hardware.pumped_litres_per_round)

        assert 0 <= rps <= 70, f"rps have to be between 0 and 70 (passed {rps})"
        self.control_pin.value = rps / 70
        self.desired_rps_queue.put((time.time(), rps))

    def check_errors(self) -> None:
        """checks whether the pump behaves incorrectly - Possibly
        raises the  PumpInterface.DeviceFailure exception"""
        if self.config.active_components.pump_speed_monitoring:
            if self.rps_monitoring_process.is_alive():
                self.logger.info("pump doesn't report any errors")
            else:
                try:
                    raise PumpInterface.DeviceFailure(
                        self.rps_monitoring_exceptions.get_nowait()
                    )
                except queue.Empty:
                    raise PumpInterface.DeviceFailure(
                        "rps monitoring process has stopped without an exception"
                    )

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.set_desired_pump_speed(unit="rps", value=0)

        if self.rps_monitoring_process is not None:
            if self.rps_monitoring_process.is_alive():
                self.rps_monitoring_process.terminate()

        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {PUMP_CONTROL_PIN_OUT} 0")

    @staticmethod
    def monitor_rps(
        config: custom_types.Config,
        rps_measurement_queue: queue.Queue[float],
        desired_rps_queue: queue.Queue[tuple[float, float]],
        rps_monitoring_exceptions: queue.Queue[str],
    ) -> None:
        """monitors the rps of the pump interface. this function
        is blocking, hence it is started in a thread"""

        logger = utils.Logger(origin="pump-rps-monitoring")
        current_rps_update_time = time.time()
        current_rps: float = 0

        while True:
            time.sleep(10)

            # expected roundes computed from the "desired rps" setting
            # and the respective time between rps updates
            expected_rounds: float = 0
            try:
                new_rps_update_time, new_rps = desired_rps_queue.get_nowait()
                expected_rounds += (
                    new_rps_update_time - current_rps_update_time
                ) * current_rps
                current_rps_update_time, current_rps = new_rps_update_time, new_rps
            except queue.Empty:
                break

            # the 10 seconds of sleep time do not have to be exact
            # because the latest desired-rps-block is using the exact
            # time anyway
            now = time.time()
            expected_rounds += (now - current_rps_update_time) * current_rps
            current_rps_update_time = now

            # the actual rounds since the last rps-monitoring loop are
            # counted by counting how many times the speed pin received
            # a change from low to high since the last loop
            actual_rounds: float = 0
            while True:
                try:
                    rps_measurement_queue.get_nowait()
                    actual_rounds += 1
                except queue.Empty:
                    break
            actual_rounds /= 18

            # consequences from the measurement
            difference_in_percent = round(
                ((actual_rounds - expected_rounds) * 100) / expected_rounds,
                2,
            )
            if -7.5 < difference_in_percent < 7.5:
                logger.debug(
                    f"pump speed varies by ± {difference_in_percent}%"
                    + " target (in good range)"
                )
            elif -15 < difference_in_percent < 15:
                logger.warning(
                    f"pump speed varies by ± {difference_in_percent}%"
                    + " target (in noticeable range)",
                    config=config,
                )
            else:
                error_message = (
                    f"pump speed varies by ± {difference_in_percent}%"
                    + " target (in unaccpetable range)"
                )
                logger.error(error_message, config=config)

                # this queue will make the main thread raise an exception
                rps_monitoring_exceptions.put(error_message)

                return
