import serial
from src import utils, types
import gpiozero
import gpiozero.pins.pigpio


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
        separate_messages = self.current_input_stream.split("\n")
        self.current_input_stream = separate_messages[-1]
        return separate_messages[:-1]


class WindSensorInterface:
    messages = []

    def __init__(self, config: types.Config, logger: utils.Logger | None = None) -> None:
        self.rs232_interface = RS232Interface()
        self.logger = logger if logger is not None else utils.Logger(config, origin="co2-sensor")
        self.pin_factory = utils.get_pin_factory()
        self.power_pin = gpiozero.OutputDevice(
            pin=utils.Constants.wind_sensor.power_pin_out, pin_factory=self.pin_factory
        )
        self.power_pin.on()

    def update(self) -> None:
        WindSensorInterface.messages += self.rs232_interface.get_messages()

    def get_current_values(self) -> None:
        self.update()
        print(WindSensorInterface.messages)

    def teardown(self) -> None:
        """End all hardware connections"""
        self.power_pin.off()
        self.pin_factory.close()
