import time
import serial
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
    + f"Vs={number_regex}V,Vr={number_regex}V,Id=tumesmmw\d+$"
)


class RS232Interface:
    def __init__(self) -> None:
        self.serial_interface = serial.Serial(
            port=utils.Constants.wind_sensor.serial_port,
            baudrate=19200,
            bytesize=8,
            parity="N",
            stopbits=1,
        )
        self.current_input_stream = ""

    def get_messages(self) -> list[str]:
        new_input_bytes = self.serial_interface.read_all()
        if new_input_bytes is None:
            return []

        self.current_input_stream += new_input_bytes.decode("cp1252")
        separate_messages = self.current_input_stream.split("\r\n")
        self.current_input_stream = separate_messages[-1]
        return separate_messages[:-1]


class WindSensorInterface:
    class DeviceFailure(Exception):
        """raised when the wind sensor either reports
        low voltage or has not sent any data in a while"""

    def __init__(
        self, config: custom_types.Config, logger: utils.Logger | None = None
    ) -> None:
        self.rs232_interface = RS232Interface()
        self.logger = (
            logger if logger is not None else utils.Logger(config, origin="co2-sensor")
        )
        self.pin_factory = utils.get_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=utils.Constants.wind_sensor.power_pin_out, pin_factory=self.pin_factory
        )
        self.power_pin.on()

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
        # TODO: log warning when last update time on each reaches a certain threshold

    def get_current_wind_measurement(self) -> custom_types.WindSensorData | None:
        self._update_current_values()
        return self.wind_measurement

    def get_current_device_status(self) -> custom_types.WindSensorStatus | None:
        self._update_current_values()
        return self.device_status

    def teardown(self) -> None:
        """End all hardware connections"""
        self.power_pin.off()
        self.pin_factory.close()

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
