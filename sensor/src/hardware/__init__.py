import filelock

from src import custom_types, utils
from .bme280_sensor import BME280SensorInterface
from .co2_sensor import CO2SensorInterface
from .pump import PumpInterface
from .sht45_sensor import SHT45SensorInterface
from .ups import UPSInterface
from .valves import ValveInterface
from .wind_sensor import WindSensorInterface

# global lock over all software versions
hardware_lock = filelock.FileLock(
    "/home/pi/Documents/hermes/hermes-hardware.lock", timeout=5
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
        self.config = config
        self.logger = utils.Logger(
            "hardware-interface",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.testing = testing
        self.acquire_hardware_lock()

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

        if not hardware_lock.is_locked:
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
        hardware_lock.release()

    def reinitialize(self, config: custom_types.Config) -> None:
        """reinitialize after an unsuccessful update"""
        self.config = config
        self.logger.info("running hardware reinitialization")
        self.acquire_hardware_lock()

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

    def acquire_hardware_lock(self) -> None:
        """make sure that there is only one initialized hardware connection"""
        try:
            hardware_lock.acquire()
        except filelock.Timeout:
            raise HardwareInterface.HardwareOccupiedException(
                "hardware occupied by another process"
            )
