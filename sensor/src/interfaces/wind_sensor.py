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

        self.wind_measurement: types.WindSensorData | None = None
        self.device_status: types.WindSensorStatus | None = None

    def _update_current_values(self) -> None:
        new_messages = self.rs232_interface.get_messages()
        now = round(time.time())
        for m in new_messages:
            if measurement_pattern.match(m) is not None:
                parsed_message = "".join(c for c in m[4:] if c.isnumeric() or c in [",", "."])
                dn, dm, dx, sn, sm, sx = [float(v) for v in parsed_message.split(",")]
                self.wind_measurement = types.WindSensorData(
                    direction_min=dn,
                    direction_avg=dm,
                    direction_max=dx,
                    speed_min=sn,
                    speed_avg=sm,
                    speed_max=sx,
                    last_update_time=now,
                )
            if device_status_pattern.match(m) is not None:
                parsed_message = "".join(c for c in m[4:-13] if c.isnumeric() or c in [",", "."])
                th, vh, vs, vr = [float(v) for v in parsed_message.split(",")]
                self.device_status = types.WindSensorStatus(
                    temperature=th,
                    heating_voltage=vh,
                    supply_voltage=vs,
                    reference_voltage=vr,
                    sensor_id=m.split("=")[-1],
                    last_update_time=now,
                )
        # TODO: log warning when last update time on each reaches a certain threshold

    def get_current_wind_measurement(self) -> types.WindSensorData | None:
        self._update_current_values()
        return self.wind_measurement

    def get_current_device_status(self) -> types.WindSensorData | None:
        self._update_current_values()
        return self.device_status

    def teardown(self) -> None:
        """End all hardware connections"""
        self.power_pin.off()
        self.pin_factory.close()

    # TODO: Add report_issues function
    #       1. are both data entries not too old
    #       2. does the system state report reasonable voltage data
