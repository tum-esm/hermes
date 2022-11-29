import time
import serial
from src import utils, types
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
    def __init__(self, config: types.Config, logger: utils.Logger | None = None) -> None:
        self.rs232_interface = RS232Interface()
        self.logger = logger if logger is not None else utils.Logger(config, origin="co2-sensor")
        self.pin_factory = utils.get_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=utils.Constants.wind_sensor.power_pin_out, pin_factory=self.pin_factory
        )
        self.power_pin.on()

        self.last_wind_measurement: str | None = None
        self.last_wind_measurement_time: float | None = None
        self.last_device_status: str | None = None
        self.last_device_status_time: float | None = None

    def update(self) -> None:
        new_messages = self.rs232_interface.get_messages()
        now = time.time()
        for m in new_messages:
            if measurement_pattern.match(m) is not None:
                self.last_wind_measurement_time = now
                self.last_wind_measurement = m
            if device_status_pattern.match(m) is not None:
                self.last_device_status_time = now
                self.last_device_status = m

    def get_current_values(self) -> None:
        self.update()
        print(f"measurement: {self.last_wind_measurement}")
        print(f"device status: {self.last_device_status}")

    def teardown(self) -> None:
        """End all hardware connections"""
        self.power_pin.off()
        self.pin_factory.close()
