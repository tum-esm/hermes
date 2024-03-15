import os
from typing import TypedDict

import filelock

from src import custom_types, utils
from .bme280_sensor import BME280SensorInterface
from .co2_sensor import CO2SensorInterface
from .pump import PumpInterface
from .sht45_sensor import SHT45SensorInterface
from .ups import UPSInterface
from .valves import ValveInterface
from .wind_sensor import WindSensorInterface


class HwLock(TypedDict):
    lock: filelock.FileLock


global_hw_lock: HwLock = {
    "lock": filelock.FileLock("")
}


def acquire_hardware_lock() -> None:
    """make sure that there is only one initialized hardware connection"""
    try:
        global_hw_lock["lock"].acquire()
    except filelock.Timeout:
        raise HardwareInterface.HardwareOccupiedException(
            "hardware occupied by another process"
        )


class HardwareInterface:
    class HardwareOccupiedException(Exception):
        """raise when trying to use the hardware, but it
        is used by another process"""

    def __init__(
            self,
            config: custom_types.Config,
            testing: bool = False,
    ) -> None:
        global_hw_lock["lock"] = filelock.FileLock(
            os.environ.get("HARDWARE_LOCKFILE_PATH") or "/home/pi/Documents/hermes/hermes-hardware.lock",
            timeout=5
        )
        self.config = config
        self.logger = utils.Logger(
            "hardware-interface",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.testing = testing
        acquire_hardware_lock()

        # measurement sensors
        self.wind_sensor = WindSensorInterface(config, testing=self.testing)
        self.air_inlet_bme280_sensor = BME280SensorInterface(
            config, variant="air-inlet", testing=self.testing
        )
        self.air_inlet_sht45_sensor = SHT45SensorInterface(config, testing=self.testing)
        self.co2_sensor = CO2SensorInterface(config, testing=self.testing)

        # measurement actors
        self.pump = PumpInterface(config, testing=self.testing)
        self.valves = ValveInterface(config, testing=self.testing)

        # enclosure controls
        self.mainboard_sensor = BME280SensorInterface(
            config, variant="mainboard", testing=self.testing
        )
        self.ups = UPSInterface(config, testing=self.testing)

    def check_errors(self) -> None:
        """checks for detectable hardware errors"""
        self.logger.info("checking for hardware errors")
        self.co2_sensor.check_errors()
        self.wind_sensor.check_errors()

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.logger.info("running hardware teardown")

        if not global_hw_lock["lock"].is_locked:
            self.logger.info("not tearing down due to disconnected hardware")
            return

        # measurement sensors
        self.air_inlet_bme280_sensor.teardown()
        self.wind_sensor.teardown()

        # measurement actors
        self.pump.teardown()
        self.valves.teardown()
        self.co2_sensor.teardown()

        # enclosure controls
        self.mainboard_sensor.teardown()
        self.ups.teardown()

        # release lock
        global_hw_lock["lock"].release()

    def reinitialize(self, config: custom_types.Config) -> None:
        """reinitialize after an unsuccessful update"""
        self.config = config
        self.logger.info("running hardware reinitialization")
        acquire_hardware_lock()

        # measurement sensors
        self.air_inlet_bme280_sensor = BME280SensorInterface(
            config, variant="air-inlet", testing=self.testing
        )
        self.air_inlet_sht45_sensor = SHT45SensorInterface(config, testing=self.testing)
        self.co2_sensor = CO2SensorInterface(config, testing=self.testing)
        self.wind_sensor = WindSensorInterface(config, testing=self.testing)

        # measurement actors
        self.pump = PumpInterface(config, testing=self.testing)
        self.valves = ValveInterface(config, testing=self.testing)

        # enclosure controls
        self.mainboard_sensor = BME280SensorInterface(
            config, variant="mainboard", testing=self.testing
        )
        self.ups = UPSInterface(config, testing=self.testing)
