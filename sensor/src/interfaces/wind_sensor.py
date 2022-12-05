import time
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


class WindSensorInterface:
    class DeviceFailure(Exception):
        """raised when the wind sensor either reports
        low voltage or has not sent any data in a while"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(config, origin="co2-sensor")
        self.config = config

        self.pin_factory = utils.gpio.get_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=utils.Constants.WindSensor.power_pin_out, pin_factory=self.pin_factory
        )
        self.power_pin.on()

        self.rs232_interface = utils.serial_interfaces.SerialWindSensorInterface(
            port=utils.Constants.WindSensor.serial_port
        )
        self.wind_measurement: custom_types.WindSensorData | None = None
        self.device_status: custom_types.WindSensorStatus | None = None

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

    def get_current_wind_measurement(self) -> custom_types.WindSensorData | None:
        self._update_current_values()
        return self.wind_measurement

    def get_current_device_status(self) -> custom_types.WindSensorStatus | None:
        self._update_current_values()
        return self.device_status

    def check_sensor_errors(self) -> None:
        """checks whether the wind sensor behaves incorrectly - Possibly
        raises the WindSensorInterface.DeviceFailure exception"""

        now = time.time()

        if self.wind_measurement is not None:
            if now - self.wind_measurement.last_update_time > 120:
                raise WindSensorInterface.DeviceFailure(
                    "last wind measurement data is older than two minutes"
                    + f" ({self.wind_measurement})"
                )

        if self.device_status is not None:
            if now - self.device_status.last_update_time > 120:
                raise WindSensorInterface.DeviceFailure(
                    "last device status data is older than two minutes"
                    + f" ({self.device_status})"
                )
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

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.power_pin.off()
        self.pin_factory.close()
