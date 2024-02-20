import filelock
from src import custom_types, utils

from .co2_sensor import CO2SensorInterface
from .bme280_sensor import BME280SensorInterface
from .sht45_sensor import SHT45SensorInterface
from .pump import PumpInterface
from .ups import UPSInterface
from .valves import ValveInterface
from .wind_sensor import WindSensorInterface


class HardwareInterface:
    class HardwareOccupiedException(Exception):
        """raise when trying to use the hardware, but it
        is used by another process"""

    def __init__(
        self,
        config: custom_types.Config,
        testing: bool = False,
    ) -> None:
        self.hardware_lock = filelock.FileLock(config.hardware_lockfile_path, timeout=5)
        self.config = config
        self.logger = utils.Logger(
            "hardware-interface",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.testing = testing
        self.acquire_hardare_lock()

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

        if not self.hardware_lock.is_locked:
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
        self.hardware_lock.release()

    def reinitialize(self, config: custom_types.Config) -> None:
        """reinitialize after an unsuccessful update"""
        self.config = config
        self.logger.info("running hardware reinitialization")
        self.acquire_hardare_lock()

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

    def acquire_hardare_lock(self) -> None:
        """make sure that there is only one initialized hardware connection"""
        try:
            self.hardware_lock.acquire()
        except filelock.Timeout:
            raise HardwareInterface.HardwareOccupiedException(
                "hardware occupied by another process"
            )
