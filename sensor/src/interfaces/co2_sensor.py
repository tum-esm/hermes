from datetime import datetime
import queue
from typing import Literal
import serial
import time
import threading
from src import utils, types


# TODO: add pressure calibration
# TODO: add humidity calibration
# TODO: add oxygen calibration
# TODO: add temperature calibration
# TODO: verify received CO2 values with regex


class RS232Interface:
    receiving_queue: queue.Queue[str] = queue.Queue()

    def __init__(self) -> None:
        self.serial_interface = serial.Serial("/dev/ttySC0", 19200)

    def write(
        self,
        message: str,
        sleep: float | None = None,
        send_esc: bool = False,
        save_eeprom: bool = False,
    ) -> None:
        # TODO: add thread lock
        self.serial_interface.write(
            (("\x1B " if send_esc else "") + message + "\r\n").encode("utf-8")
        )
        if save_eeprom:
            self.rs232_interface.write("save\r\n".encode("utf-8"))
        self.serial_interface.flush()
        if sleep is not None:
            time.sleep(sleep)

    def read(self) -> str:
        # TODO: add thread lock
        waiting_bytes_count = self.serial_interface.inWaiting()
        if waiting_bytes_count > 0:
            received_bytes = self.serial_interface.read(waiting_bytes_count)
            if received_bytes[0] != 0:
                return received_bytes.decode("cp1252").replace(";", ",")
        return ""

    @staticmethod
    def data_receiving_loop():
        """Receiving all the data that is send over RS232 and print it.
        If the data is a CO2 measurement it will be safed in sensor log
        """
        accumulating_serial_stream = ""
        rs232_interface = RS232Interface()
        while True:
            accumulating_serial_stream += rs232_interface.read()
            splitted_serial_stream = accumulating_serial_stream.split("\n")
            for received_line in splitted_serial_stream[:-1]:
                RS232Interface.receiving_queue.put(received_line)
            accumulating_serial_stream = splitted_serial_stream[-1]

            time.sleep(0.001)


class CO2SensorInterface:
    def __init__(self, config: types.Config) -> None:
        self.rs232_interface = RS232Interface()
        self.logger = utils.Logger(config, origin="co2-sensor")

    def start_polling_measurements(self):
        self.rs232_interface.write("r", sleep=0.1)
        self.logger.info("started polling")

    def stop_polling_measurements(self):
        self.rs232_interface.write("s", sleep=0.1)
        self.logger.info("stopped polling")

    def start_receiving_data(self):
        """Start new thread for the receiving data over RS232
        it is a deamon thread that will be ended if the main thread is killed
        """
        threading.Thread(target=RS232Interface.data_receiving_loop, daemon=True).start()
        # TODO: log

    def set_filter_setting(
        self,
        median: int = 0,
        average: int = 10,
        smooth: int = 0,
        linear: bool = True,
        save_eeprom: bool = False,
    ):
        """Send the command for the filter settings
        Median first filters in chain, removing random peak values. Number of
        measurements is set by Median command (0 to 13 measurments)
        Averaging filter calculates moving average over period of time.
        Can be set from 0 to 60 seconds for longer averaging times use smoothing.
        0s => 3ppm; 10s => 2ppm; 30s => 1ppm
        Smoothing filter calculates the running average by weighting
            the most recent measurments.
        It is a factor that can be set between 0 to 255 and is calculated as follows:
            Smooting factor * 4 = approx. averaging time(s)
        The CO2 sensor is producing a signal which is not liear to the CO2 concentration
        The user can disable the internal linearization to achieve
            a signal proportioal to the absorption (True or False)
        """
        assert average >= 0 and average <= 60, "invalid calibration setting, average not in [0, 60]"
        assert smooth >= 0 and smooth <= 255, "invalid calibration setting, smooth not in [0, 255]"
        assert median >= 0 and median <= 13, "invalid calibration setting, median not in [0, 13]"

        self.rs232_interface.write(f"average {average}", send_esc=True)
        self.rs232_interface.write(f"smooth {smooth}", send_esc=True)
        self.rs232_interface.write(f"median {median}", send_esc=True)
        self.rs232_interface.write(
            f"linear {'on' if linear else 'off'}", send_esc=True, save_eeprom=save_eeprom, sleep=0.5
        )

        # TODO: log

    def set_measurement_interval(
        self,
        value: int = 1,
        unit: Literal["s", "min", "h"] = "s",
        save_eeprom: bool = False,
    ) -> None:
        """Send the command to set the time between the automatic measurment
        value can be selected between 1 to 1000."""

        assert 1 <= value <= 1000, "invalid interval setting"
        self.rs232_interface.write(f"intv {value} {unit}", save_eeprom=save_eeprom, sleep=0.2)

        # TODO: log

    def set_time(self, save_eeprom: bool = False) -> None:
        """The function set the time of the CO2"""
        self.rs232_interface.write(
            f"time {datetime.now().strftime('%H:%M:%S')}",
            send_esc=True,
            save_eeprom=save_eeprom,
            sleep=0.1,
        )
        # TODO: log

    def get_time(self) -> str:
        """The function get the time of the CO2 Sensor since the last reset.
        return: String in the format of "12:10:04"
        """
        # TODO: possibly stop co2 measurements
        # TODO: flush receiver cache

        self.rs232_interface.write("time", sleep=0.1)

        # TODO: read receiver queue
        # TODO: possibly restart co2 measurements
        # TODO: log

        return "hh:mm:ss"

    def set_measurement_range(
        self,
        upper_limit: Literal[1000, 2000, 3000, 4000, 5000, 20000] = 1000,
        save_eeprom: bool = False,
    ) -> None:
        """Set the measurement range of the sensors"""
        self.rs232_interface.write(
            f"range {upper_limit}", send_esc=True, save_eeprom=save_eeprom, sleep=1
        )
        # TODO: log

    def set_formatting_message(
        self,
        raw_data: bool = True,
        with_compensation_data: bool = True,
        filtered_data: bool = True,
        echo: bool = True,
        save_eeprom: bool = False,
    ) -> None:
        """Send the commands to format the measurement messages
        raw_data is the raw data before any compensations and filters (True or False)
        with_compensation_data is the data before the filters but with the
        enabled compensations like oxygen, humidity (True or False)
        filtered_data is the data after the compensations and enabled filters (True or False)
        echo defines if the sensor returns the sended commands (True or False)
        """
        # TODO: possibly stop co2 measurements
        # TODO: flush receiver cache

        format_list: list[str] = []
        if raw_data:
            format_list.append('"Raw"CO2RAWUC"ppm"')
        if with_compensation_data:
            format_list.append('"Comp"CO2RAW"ppm"')
        if filtered_data:
            format_list.append('"Filt"CO2"ppm"')
        formatting_string = "form " + ("; ".join(format_list)) + "#r#n"

        self.rs232_interface.write(formatting_string, send_esc=True)
        self.rs232_interface.write(
            f"echo {'on' if echo else 'off'}", send_esc=True, save_eeprom=save_eeprom, sleep=1
        )

        # TODO: possibly restart co2 measurements
        # TODO: log

    def get_info(
        self,
        device_info: bool = True,
        software_version: bool = False,
        errors: bool = False,
        corrections: bool = False,
    ) -> str:
        """Send diffrent information about the versions and settings of the CO2 sensor
        device_info shows name/software version, serien number, last calibration,
            measurment span, pressure, humidity, oxygen, compensations, interface
        software_version shows software version (also in device_info)
        errors shows the error messages that are received
        corrections shows the last linear and multipoint correction value
        return: string of the complete answer of the CO2 sensor
        """
        # TODO: possibly stop co2 measurements
        # TODO: flush receiver cache

        if device_info:
            self.rs232_interface.write("??")
        if software_version:
            self.rs232_interface.write("vers")
        if errors:
            self.rs232_interface.write("errs")
        if corrections:
            self.rs232_interface.write("corr")

        time.sleep(1)

        # TODO: receive infos
        # TODO: possibly restart co2 measurements
        # TODO: log

        return "something"