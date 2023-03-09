import multiprocessing
import time
from typing import Optional
import filelock
from src import custom_types, utils

from .air_inlet_sensor import AirInletSensorInterface
from .co2_sensor import CO2SensorInterface
from .heated_enclosure import HeatedEnclosureInterface
from .mainboard_sensor import MainboardSensorInterface
from .pump import PumpInterface
from .ups import UPSInterface
from .usb_ports import USBPortInterface
from .valves import ValveInterface
from .wind_sensor import WindSensorInterface

# global lock over all software versions
hardware_lock = filelock.FileLock(
    "/home/pi/Documents/hermes/hermes-hardware.lock", timeout=5
)


class HardwareInterface:
    class HardwareOccupiedException(Exception):
        """raise when trying to use the hardware but it
        is used by another process"""

    def __init__(self, config: custom_types.Config) -> None:
        self.config = config
        self.logger = utils.Logger("hardware-interface")
        self.acquire_hardare_lock()

        # measurement sensors
        self.air_inlet_sensor = AirInletSensorInterface(config)
        self.co2_sensor = CO2SensorInterface(config)
        self.wind_sensor = WindSensorInterface(config)

        # measurement actors
        self.pump = PumpInterface(config)
        self.valves = ValveInterface(config)

        # enclosure controls
        self.mainboard_sensor = MainboardSensorInterface(config)
        self.ups = UPSInterface(config)

        # heated enclosure communication with repairing
        # routine is running in a separate thread
        if self.config.active_components.heated_enclosure_communication:
            HeatedEnclosureThread.init(config)
        else:
            self.logger.debug("skipping heated enclosure communication")

    def check_errors(self) -> None:
        """checks for detectable hardware errors"""
        self.logger.info("checking for hardware errors")
        self.co2_sensor.check_errors()
        self.wind_sensor.check_errors()
        self.pump.check_errors()
        self.mainboard_sensor.check_errors()
        HeatedEnclosureThread.check_errors()

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.logger.info("running hardware teardown")

        if not hardware_lock.is_locked:
            self.logger.info("not tearing down due to disconnected hardware")
            return

        # measurement sensors
        self.air_inlet_sensor.teardown()
        self.co2_sensor.teardown()
        self.wind_sensor.teardown()

        # measurement actors
        self.pump.teardown()
        self.valves.teardown()

        # enclosure controls
        self.mainboard_sensor.teardown()
        self.ups.teardown()
        HeatedEnclosureThread.deinit()

        # release lock
        hardware_lock.release()

    def reinitialize(self, config: custom_types.Config) -> None:
        """reinitialize after an unsuccessful update"""
        self.config = config
        self.logger.info("running hardware reinitialization")
        self.acquire_hardare_lock()

        # measurement sensors
        self.air_inlet_sensor = AirInletSensorInterface(config)
        self.co2_sensor = CO2SensorInterface(config)
        self.wind_sensor = WindSensorInterface(config)

        # measurement actors
        self.pump = PumpInterface(config)
        self.valves = ValveInterface(config)

        # enclosure controls
        self.mainboard_sensor = MainboardSensorInterface(config)
        self.ups = UPSInterface(config)
        HeatedEnclosureThread.init(config)

    def acquire_hardare_lock(self) -> None:
        """make sure that there is only one initialized hardware connection"""
        try:
            hardware_lock.acquire()
        except filelock.Timeout:
            raise HardwareInterface.HardwareOccupiedException(
                "hardware occupied by another process"
            )


class HeatedEnclosureThread:
    communication_loop_process: Optional[multiprocessing.Process] = None

    @staticmethod
    def init(config: custom_types.Config) -> None:
        """start the archiving loop and the communication loop
        in two separate processes"""

        if HeatedEnclosureThread.communication_loop_process is not None:
            if not HeatedEnclosureThread.communication_loop_process.is_alive():
                HeatedEnclosureThread.archiving_loop_process.join()

        new_process = multiprocessing.Process(
            target=HeatedEnclosureThread.communcation_loop,
            args=(config,),
            daemon=True,
        )
        new_process.start()
        HeatedEnclosureThread.communication_loop_process = new_process

    @staticmethod
    def deinit() -> None:
        """stop the archiving loop and the communication loop"""

        if HeatedEnclosureThread.archiving_loop_process is not None:
            HeatedEnclosureThread.archiving_loop_process.terminate()
            HeatedEnclosureThread.archiving_loop_process.join()
            HeatedEnclosureThread.archiving_loop_process = None

    @staticmethod
    def communication_loop(config: custom_types.Config) -> None:
        heated_enclosure: Optional[HeatedEnclosureInterface] = None

        usb_ports = USBPortInterface()
        active_mqtt_queue = utils.ActiveMQTTQueue()
        logger = utils.Logger("heated-enclosure-thread")

        last_init_time = 0
        last_datapoint_time = 0
        exception_is_present = False

        while True:
            time_remaining_to_next_datapoint = (
                config.heated_enclosure.seconds_per_stored_datapoint
                - (time.time() - last_datapoint_time)
            )
            if time_remaining_to_next_datapoint > 0:
                time.sleep(time_remaining_to_next_datapoint)

            try:
                now = time.time()

                if heated_enclosure is None:
                    heated_enclosure = HeatedEnclosureInterface(config)
                    last_init_time = now

                measurement = heated_enclosure.get_current_measurement()
                last_datapoint_time = now

                if measurement is None:
                    if (now - last_init_time) < 120:
                        continue
                    raise TimeoutError(
                        "Arduino still didn't send anything "
                        + "two minutes after initialization"
                    )

                if (now - measurement.last_update_time) > 120:
                    raise TimeoutError(
                        "Arduino didn't send anything for the last two minutes"
                    )

                if measurement.measured is None:
                    logger.warning(
                        "enclosure temperature sensor not connected",
                        config=config,
                    )
                else:
                    if measurement.measured > 50:
                        logger.warning(
                            "high temperatures inside heated enclosure: "
                            + f"{measurement.measured} °C",
                            config=config,
                        )

                logger.debug(
                    f"heated enclosure measurement: temperature is {measurement.measured} °C, "
                    + f"heater is {'on' if measurement.heater_is_on else 'off'}, "
                    + f"fan is {'on' if measurement.fan_is_on else 'off'}"
                )
                active_mqtt_queue.enqueue_message(
                    config,
                    custom_types.MQTTDataMessageBody(
                        revision=config.revision,
                        timestamp=round(time.time(), 2),
                        value=custom_types.MQTTEnclosureData(
                            variant="enclosure",
                            data=measurement,
                        ),
                    ),
                )

                exception_is_present = False

            except:
                # only log exceptions when they are newly occuring
                if not exception_is_present:
                    logger.exception(
                        label="new error in heated enclosure thread",
                        config=config,
                    )
                    exception_is_present = True

                if heated_enclosure is not None:
                    heated_enclosure.teardown()

                logger.info("waiting two minutes until trying again")
                usb_ports.toggle_usb_power(delay=30)
                time.sleep(90)

    @staticmethod
    def check_errors() -> None:
        """Raises an `MessagingAgent.CommuncationOutage` exception
        if communication loop processes is not running."""

        if not HeatedEnclosureThread.communication_loop_process.is_alive():
            raise HeatedEnclosureThread.CommuncationOutage(
                "communication loop process is not running"
            )
