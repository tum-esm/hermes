import time
from typing import Optional
from src import utils, custom_types
import gpiozero
import gpiozero.pins.pigpio
import re

measurement_pattern = (
    pattern
) = r"Dn=([0-9.]+)D,Dm=([0-9.]+)D,Dx=([0-9.]+)D,Sn=([0-9.]+)M,Sm=([0-9.]+)M,Sx=([0-9.]+)M"
device_status_pattern = r"Th=([0-9.]+)C,Vh=([0-9.]+)N,Vs=([0-9.]+)V,Vr=([0-9.]+)V"


WIND_SENSOR_POWER_PIN_OUT = 21
WIND_SENSOR_SERIAL_PORT = "/dev/ttySC1"


class WindSensorInterface:
    class DeviceFailure(Exception):
        """raised when the wind sensor either reports
        low voltage or has not sent any data in a while"""

    def __init__(
        self,
        config: custom_types.Config,
        testing: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            origin="wind-sensor",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.config = config

        self.logger.info("Starting initialization")
        self.wind_measurement: Optional[custom_types.WindSensorData] = None
        self.device_status: Optional[custom_types.WindSensorStatus] = None

        # power pin to power up/down wind sensor
        self.pin_factory = utils.get_gpio_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=WIND_SENSOR_POWER_PIN_OUT,
            pin_factory=self.pin_factory,
        )
        self.power_pin.on()

        # serial connection to receive data from wind sensor
        self.wxt532_interface = utils.serial_interfaces.SerialOneDirectionalInterface(
            port=WIND_SENSOR_SERIAL_PORT,
            baudrate=19200,
            encoding="cp1252",
            line_endling="\r\n",
        )

        self.logger.info("Finished initialization")

    def _update_current_values(self) -> None:
        new_messages = self.wxt532_interface.get_messages()
        now = round(time.time())
        for message in new_messages:
            # TODO: Average over all valid messages of the last 2 minutes
            # TODO: Don't average for Min/Max
            # Check if there's a match for the measurement_pattern
            measurement_match = re.search(measurement_pattern, message)
            if measurement_match is not None:
                # Extract the values using group() method
                self.wind_measurement = custom_types.WindSensorData(
                    direction_min=measurement_match.group(1),
                    direction_avg=measurement_match.group(2),
                    direction_max=measurement_match.group(3),
                    speed_min=measurement_match.group(4),
                    speed_avg=measurement_match.group(5),
                    speed_max=measurement_match.group(6),
                    last_update_time=now,
                )

            # Check if there's a match for the device_status_pattern
            device_match = re.search(device_status_pattern, message)
            if device_match is not None:
                # Extract the values using group() method
                self.device_status = custom_types.WindSensorStatus(
                    temperature=device_match.group(1),
                    heating_voltage=device_match.group(2),
                    supply_voltage=device_match.group(3),
                    reference_voltage=device_match.group(4),
                    last_update_time=now,
                )

    def get_current_wind_measurement(self) -> Optional[custom_types.WindSensorData]:
        self._update_current_values()
        return self.wind_measurement

    def get_current_device_status(self) -> Optional[custom_types.WindSensorStatus]:
        self._update_current_values()
        return self.device_status

    def check_errors(self) -> None:
        """checks whether the wind sensor behaves incorrectly - Possibly
        raises the WindSensorInterface.DeviceFailure exception"""

        now = time.time()
        self._update_current_values()

        if self.device_status is not None:
            # only consider values less than 5 minutes old
            if (now - self.device_status.last_update_time) < 300:
                if not (22 <= self.device_status.heating_voltage <= 26):
                    raise WindSensorInterface.DeviceFailure(
                        "the heating voltage is off by more than 2 volts"
                        + f" ({self.device_status})"
                    )
                if not (22 <= self.device_status.supply_voltage <= 26):
                    raise WindSensorInterface.DeviceFailure(
                        "the supply voltage is off by more than 2 volts"
                        + f" ({self.device_status})"
                    )
                if not (3.2 <= self.device_status.reference_voltage <= 4.0):
                    raise WindSensorInterface.DeviceFailure(
                        "the reference voltage is off by more than 0.4 volts"
                        + f" ({self.device_status})"
                    )

                self.logger.info("the wind sensor check doesn't report any errors")
        else:
            self.logger.info("no wind sensor seems to be connected")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.power_pin.off()
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {WIND_SENSOR_POWER_PIN_OUT} 0")
