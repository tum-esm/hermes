import time
from typing import Optional
from src import utils, custom_types
import gpiozero
import gpiozero.pins.pigpio
import re

number_regex = r"\d+(\.\d+)?"
measurement_pattern = re.compile(
    f"^0R1,Dn={number_regex}D,Dm={number_regex}D,Dx={number_regex}D,"
    + f"Sn={number_regex}M,Sm={number_regex}M,Sx={number_regex}M$"
)
device_status_pattern = re.compile(
    f"^0R5,Th={number_regex}C,Vh={number_regex}N,"
    + f"Vs={number_regex}V,Vr={number_regex}V,Id=tumesmmw\\d+$"
)


WIND_SENSOR_POWER_PIN_OUT = 21
WIND_SENSOR_SERIAL_PORT = "/dev/ttySC1"


class WindSensorInterface:
    class DeviceFailure(Exception):
        """raised when the wind sensor either reports
        low voltage or has not sent any data in a while"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger, self.config = utils.Logger(origin="wind-sensor"), config
        self.logger.info("Starting initialization")

        # power pin to power up/down wind sensor
        self.pin_factory = utils.get_gpio_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=WIND_SENSOR_POWER_PIN_OUT,
            pin_factory=self.pin_factory,
        )
        self.power_pin.on()

        # serial connection to receive data from wind sensor
        self.rs232_interface = utils.serial_interfaces.SerialOneDirectionalInterface(
            port=WIND_SENSOR_SERIAL_PORT,
            baudrate=19200,
            encoding="cp1252",
            line_endling="\r\n",
        )
        self.wind_measurement: Optional[custom_types.WindSensorData] = None
        self.device_status: Optional[custom_types.WindSensorStatus] = None

        self.logger.info("Finished initialization")

    def _update_current_values(self) -> None:
        new_messages = self.rs232_interface.get_messages()
        now = round(time.time())
        for m in new_messages:
            if measurement_pattern.match(m) is not None:
                parsed_message = "".join(
                    c for c in m[4:] if c.isnumeric() or c in [",", "."]
                )
                dn, dm, dx, sn, sm, sx = [float(v) for v in parsed_message.split(",")]
                self.wind_measurement = custom_types.WindSensorData(
                    direction_min=dn,
                    direction_avg=dm,
                    direction_max=dx,
                    speed_min=sn,
                    speed_avg=sm,
                    speed_max=sx,
                    last_update_time=now,
                )
            if device_status_pattern.match(m) is not None:
                parsed_message = "".join(
                    c for c in m[4:-13] if c.isnumeric() or c in [",", "."]
                )
                th, vh, vs, vr = [float(v) for v in parsed_message.split(",")]
                self.device_status = custom_types.WindSensorStatus(
                    temperature=th,
                    heating_voltage=vh,
                    supply_voltage=vs,
                    reference_voltage=vr,
                    sensor_id=m.split("=")[-1],
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

        if self.wind_measurement is not None:
            if (now - self.wind_measurement.last_update_time) > 120:
                self.logger.warning(
                    "last wind measurement data is older than 2 minutes"
                )
            if (now - self.wind_measurement.last_update_time) > 900:
                raise WindSensorInterface.DeviceFailure(
                    "last wind measurement data is older than 15 minutes"
                )

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

        self.logger.info("sensor doesn't report any errors")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.power_pin.off()
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {WIND_SENSOR_POWER_PIN_OUT} 0")
