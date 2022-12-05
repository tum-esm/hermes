import multiprocessing
import queue
import time
import gpiozero
import gpiozero.pins.pigpio
from src import utils, custom_types
from src.utils import Constants


class PumpInterface:
    class DeviceFailure(Exception):
        """raised when the pump either reports an rps which is off
        by more than 15% from the desired rps"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(config, "pump")
        self.config = config
        self.pin_factory = utils.gpio.get_pin_factory()

        # pins for setting desired pump speed
        self.control_pin = gpiozero.PWMOutputDevice(
            pin=Constants.Pump.control_pin_out,
            frequency=Constants.Pump.frequency,
            active_high=True,
            initial_value=0,
            pin_factory=self.pin_factory,
        )

        # queues to communicate with rps monitoring process
        self.rps_measurement_queue: queue.Queue[float] = queue.Queue()
        self.desired_rps_queue: queue.Queue[tuple[float, float]] = queue.Queue()
        self.rps_monitoring_exceptions: queue.Queue[str] = queue.Queue()

        # pins for measuring actual pump speed
        self.speed_pin = gpiozero.DigitalInputDevice(
            pin=Constants.Pump.speed_pin_in,
            pin_factory=self.pin_factory,
        )
        self.speed_pin.when_activated = lambda: self.rps_measurement_queue.put(1)

        # starting rps monitoring process
        self.rps_monitoring_process = multiprocessing.Process(
            target=PumpInterface.monitor_rps,
            args=(
                config,
                self.rps_measurement_queue,
                self.desired_rps_queue,
                self.rps_monitoring_exceptions,
            ),
        )
        self.rps_monitoring_process.start()

    def set_desired_pump_rps(self, rps: float) -> None:
        """set rps between 0 and 70"""
        assert 0 <= rps <= 70, f"rps have to be between 0 and 70 (passed {rps})"
        self.control_pin.value = rps / 70
        self.desired_rps_queue.put((time.time(), rps))

    def check_errors(self) -> None:
        """checks whether the pump behaves incorrectly - Possibly
        raises the  PumpInterface.DeviceFailure exception"""
        try:
            raise PumpInterface.DeviceFailure(
                self.rps_monitoring_exceptions.get_nowait()
            )
        except queue.Empty:
            assert (
                self.rps_monitoring_process.is_alive()
            ), "rps monitoring process has stopped without an exception"
            self.logger.info("pump doesn't report any errors")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.set_desired_pump_rps(0)
        self.rps_monitoring_process.terminate()
        self.pin_factory.close()

    @staticmethod
    def monitor_rps(
        config: custom_types.Config,
        rps_measurement_queue: queue.Queue[float],
        desired_rps_queue: queue.Queue[tuple[float, float]],
        rps_monitoring_exceptions: queue.Queue[str],
    ) -> None:
        """monitors the rps of the pump interface. this function
        is blocking, hence it is called in a thread"""

        logger = utils.Logger(config, "pump-rps-monitoring")
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
                    f"pump speed varies {difference_in_percent}%"
                    + " target (in good range)"
                )
            elif -15 < difference_in_percent < 15:
                logger.warning(
                    f"pump speed varies {difference_in_percent}%"
                    + " target (in noticeable range)"
                )
                # TODO: send warning to MQTT client
            else:
                error_message = (
                    f"pump speed varies {difference_in_percent}%"
                    + " target (in unaccpetable range)"
                )
                logger.error(error_message)

                # this queue will make the main thread raise an exception
                rps_monitoring_exceptions.put(error_message)

                return
