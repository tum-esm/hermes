from typing import Literal
import serial
import time
import fnmatch
import re
from threading import Thread
from src.utils import logger


RS232 = serial.Serial("/dev/ttySC0", 19200)

# TODO: add pressure calibration
# TODO: add humidity calibration

"""One way to improve robustness is to send an extra ESC (\x1B) character
before each command. This should ensure that GMP343 will be ready for a new command
in case of the previous command was not completed for some reason"""

class RS232Interface:
    def __init__(self) -> None:
        self.serial_interface = serial.Serial("/dev/ttySC0", 19200)
    
    def write(
        self,
        message: str,
        sleep: float | None = None,
        send_esc: bool=False,
        save_eeprom: bool = False,
    ) -> None:
        self.serial_interface.write(f"{'\x1B' if send_esc else ''}{message}\r\n".encode("utf-8"))
        if save_eeprom:
            self.rs232_interface.write("save\r\n".encode("utf-8"))
        self.serial_interface.flush()
        if sleep is not None:
            time.sleep(sleep)

class GMP343:
    thread_receiving_data = True
    last_oxygen = None
    last_pressure = None
    last_humidity = None

    def __init__(self) -> None:
        self.rs232_interface = RS232Interface()

    def set_start_polling_meas(self):
        """Send the command to start the automatic measurement
        of the CO2 sensor. The interval can be selected with INTV_setting().
        If the mode is started it has to be end with stop_polling_meas() before
        any setting can be adjusted
        """
        print("CO2 measurment has started...")
        self.rs232_interface.write("r", sleep=0.1)

    def set_stop_polling_meas(self):
        """Send the command to stop the automatic measurment
        of the CO2 sensor. More information on start_polling_meas().
        FIXME there is probably a problem with the hardware (Mainboard)
        the command "s" is correct
        """
        self.rs232_interface.write("s")
        print("CO2 measurement has stopped.")

    def get_one_measurement(self):
        """Send the command to get one measurment
        of the CO2 sensor. The function is only
        intended for formatting with all three values from the CO2 sensor (Raw, Comp, Filt)
        please refer set_formatting_message.
        return: is the three measurement values of the CO2 sensor (Raw, Comp, Filt) in an array
        """
        GMP343._receive_serial_cache(False)

        self.rs232_interface.write("send", sleep=0.3)

        received_serial_cache = GMP343._receive_serial_cache(True)

        # filter from the bytearray the actual values of the measurment
        data = [
            float(s)
            for s in re.findall(r"-?\d+\.?\d*", received_serial_cache.decode("cp1252"))
        ]

        if (
            received_serial_cache.decode("cp1252").find("ERROR") is not -1
            or len(data) < 3
        ):
            logger.error_data_logger.error(received_serial_cache.decode("cp1252"))
            return -1, -1, -1

        logger.sensor_data_logger.info(
            f"Raw  {data[0]}ppm, Comp  {data[1]}ppm, Filt  {data[2]}ppm"
        )
        print(f"Raw  {data[0]}ppm, Comp  {data[1]}ppm, Filt  {data[2]}ppm")
        return data

    def receiveing_data(self):
        """Receiving all the data that is send over RS232 and print it.
        If the data is a CO2 measurement it will be safed in sensor log
        """
        added_serial_cache = ""
        while True:
            # Wait until a other function is reading the RS232
            while not GMP343.thread_receiving_data:
                pass
            while RS232.inWaiting() > 0:
                received_serial_cache = RS232.read(RS232.inWaiting())

                if received_serial_cache[0] != 0:
                    received_serial_cache = received_serial_cache.decode("cp1252")
                    received_serial_cache = received_serial_cache.replace(";", ",")

                    print(received_serial_cache, end="")

                    added_serial_cache += received_serial_cache
                    array_serial_cache = added_serial_cache.split("\n")

                    for _ in range(len(array_serial_cache) - 1):
                        if fnmatch.fnmatch(array_serial_cache[0], "*.?ppm\r"):

                            logger.sensor_data_logger.info(array_serial_cache[0])

                        del array_serial_cache[0]
                        added_serial_cache = "\n".join(array_serial_cache)

                    received_serial_cache = bytearray(10)
            time.sleep(0.001)

    def start_receiving_data(self):
        """Start new thread for the receiving data over RS232
        it is a deamon thread that will be ended if the main thread is killed
        """
        UART_RS232_receiving = Thread(target=GMP343.receiving_data)  # creating a thread
        UART_RS232_receiving.setDaemon(True)  # change UART_RS232_receiving to daemon
        UART_RS232_receiving.start()  # starting of Thread UART_RS232_receiving

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
        assert average >= 0 and average <= 60, "Wrong calibration setting"
        assert smooth >= 0 and smooth <= 255, "Wrong calibration setting"
        assert median >= 0 and median <= 13, "Wrong calibration setting"

        self.rs232_interface.write(f"average {average}", send_esc=True)
        self.rs232_interface.write(f"smooth {smooth}", send_esc=True)
        self.rs232_interface.write(f"median {median}", send_esc=True)
        self.rs232_interface.write(f"linear {'on' if linear else 'off'}", send_esc=True)

        if save_eeprom:
            self.rs232_interface.write("save")

        time.sleep(0.5)

        # TODO: log

    def set_measurement_interval(
        self,
        value: int = 1,
        unit: Literal["s", "min", "h"] = "s",
        save_eeprom: bool = False,
    ):
        """Send the command to set the time between the automatic measurment
        value can be selected between 1 to 1000."""

        assert 1 <= value <= 1000, "invalid interval setting"
        self.rs232_interface.write(f"intv {value} {unit}")
        if save_eeprom:
           self.rs232_interface.write("save")
        time.sleep(0.2)

        # TODO: log

    @staticmethod
    def set_oxygen_calibration_setting(oxygen=20.95, save_eeprom=False):
        """Send the oxygen concentration for the compensation
        oxygen can be set between 0 and 100 (in %)
        if oxygen is None compensation is switched "off"
        save_eeprom decide if the values are saved in EEPROM of GMP343 (True or False)
        """
        assert (
            oxygen is None or oxygen >= 0 and oxygen <= 100
        ), "Wrong calibration setting"

        # The compensation is only sended if it changed or is switched off
        if oxygen is None or GMP343.last_oxygen == None:
            RS232.write(
                f"\x1B oc {'off' if oxygen == None else 'on'}\r\n".encode("utf-8")
            )
            GMP343.last_oxygen = None
            time.sleep(0.5)

        # The oxygen is only sended if it changed
        if oxygen is not None and GMP343.last_oxygen != oxygen:
            RS232.write(f"\x1B o {oxygen}\r\n".encode("utf-8"))
            GMP343.last_oxygen = oxygen
            time.sleep(0.5)

        if save_eeprom:
            RS232.write("save\r\n".encode("utf-8"))
            time.sleep(0.5)
        RS232.flush()

        logger.system_data_logger.info(
            f"Calibration setting (compensation); " + f"oxygen: {oxygen}"
        )

    @staticmethod
    def set_pressure_calibration_setting(pressure=1013, save_eeprom=False):
        """Send the atomospheric pressure for the compensation
        pressure can be set between 700 and 1300 (in hpa)
        if pressure is None compensation is switched "off"
        save_eeprom decide if the values are saved in EEPROM of GMP343 (True or False)
        """
        assert (
            pressure is None or pressure >= 700 and pressure <= 1300
        ), "Wrong calibration setting"

        # The compensation is only sended if it changed or is switched off
        if pressure is None or GMP343.last_pressure == None:
            RS232.write(
                f"\x1B pc {'off' if pressure == None else 'on'}\r\n".encode("utf-8")
            )
            GMP343.last_pressure = None
            time.sleep(0.5)

        # The pressure is only sended if it changed
        if pressure is not None and GMP343.last_pressure != pressure:
            RS232.write(f"\x1B p {pressure}\r\n".encode("utf-8"))
            GMP343.last_pressure = pressure
            time.sleep(0.5)

        if save_eeprom:
            RS232.write("save\r\n".encode("utf-8"))
            time.sleep(0.5)
        RS232.flush()

        logger.system_data_logger.info(
            f"Calibration setting (compensation); " + f"pressure: {pressure}"
        )

    @staticmethod
    def set_humidity_calibration_setting(humidity=50, save_eeprom=False):
        """Send the humidity for the compensation
        humidity can be set between 0 and 100 (in %)
        if humidity is None, compensation is switched "off"
        save_eeprom decide if the values are saved in EEPROM of GMP343 (True or False)
        """
        assert (
            humidity is None or humidity >= 0 and humidity <= 100
        ), "Wrong calibration setting"

        # The compensation is only sended if it changed or is switched off
        if humidity is None or GMP343.last_humidity == None:
            RS232.write(
                f"\x1B rhc {'off' if humidity is None else 'on'}\r\n".encode("utf-8")
            )
            GMP343.last_humidity = None
            time.sleep(0.5)

        # The humidity is only sended if it changed
        if humidity is not None and GMP343.last_humidity != humidity:
            RS232.write(f"\x1B rh {humidity}\r\n".encode("utf-8"))
            GMP343.last_humidity = humidity
            time.sleep(0.5)

        if save_eeprom:
            RS232.write("save\r\n".encode("utf-8"))
            time.sleep(0.5)
        RS232.flush()

        logger.system_data_logger.info(
            f"Calibration setting (compensation); " + f"humidity: {humidity}"
        )

    @staticmethod
    def set_temp_calibration_setting(consider=True, save_eeprom=False):
        """Switch the temperature compensation on or off
        The CO2 Sensors has an integrated temperatur sensor in the measurment chamber.
        """
        assert consider == True or consider == False, "Wrong calibration setting"
        RS232.write(f"\x1B tc {'on' if consider else 'off'}\r\n".encode("utf-8"))

        if save_eeprom:
            RS232.write("save\r\n".encode("utf-8"))
        RS232.flush()
        time.sleep(0.1)

        logger.system_data_logger.info(
            f"Calibration setting (compensation); " + f"temperature: {consider}"
        )

    @staticmethod
    def set_time(clock_time: str, save_eeprom=False):
        """The function set the time of the CO2 Sensor.
        clock time is a string like "12:15:00"
        """
        clock_time_check = list(map(int, clock_time.split(":")))
        assert (
            clock_time_check[0] >= 0
            and clock_time_check[0] < 24
            and clock_time_check[1] >= 0
            and clock_time_check[1] < 60
            and clock_time_check[2] >= 0
            and clock_time_check[2] < 60
        ), "Wrong calibration setting"
        RS232.write(f"\x1B time {clock_time}\r\n".encode("utf-8"))

        if save_eeprom:
            RS232.write("save\r\n".encode("utf-8"))
        RS232.flush()
        time.sleep(0.1)

        logger.system_data_logger.info(f"Setting clock time {clock_time}")

    @staticmethod
    def get_time():
        """The function get the time of the CO2 Sensor since the last reset.
        return: String in the format of "12:10:04"
        """
        GMP343._receive_serial_cache(False)
        time.sleep(0.05)  # max runtime of one cycle in receiving data loop

        RS232.write("time\r\n".encode("utf-8"))
        RS232.flush()
        time.sleep(0.1)

        received_serial_cache = GMP343._receive_serial_cache(True)

        return received_serial_cache[6:14].decode("cp1252")

    @staticmethod
    def set_measurement_range(span=1, save_eeprom=False):
        """Set the measurment range of the CO2 sensors
        span can be set from 1 to 6
        1 = SPAN (ppm) to 1000; 2 = SPAN (ppm) to 2000; 3 = SPAN (ppm) to 3000;
        4 = SPAN (ppm) to 4000; 5 = SPAN (ppm) to 5000; 6 = SPAN (ppm) to 20000;
        """
        assert span >= 1 and span <= 6, "Wrong calibration setting"
        RS232.write(f"\x1B range {span}\r\n".encode("utf-8"))

        if save_eeprom:
            RS232.write("save\r\n".encode("utf-8"))
        RS232.flush()
        time.sleep(1)

        logger.system_data_logger.info(
            f"Calibration setting (measurment range); " + f"span: {span}"
        )

    @staticmethod
    def set_formatting_message(
        raw_data=True,
        with_compensation_data=True,
        filtered_data=True,
        echo=True,
        save_eeprom=False,
    ):
        """Send the commands to format the measurement messages
        raw_data is the raw data before any compensations and filters (True or False)
        with_compensation_data is the data before the filters but with the
        enabled compensations like oxygen, humidity (True or False)
        filtered_data is the data after the compensations and enabled filters (True or False)
        echo defines if the sensor returns the sended commands (True or False)
        """
        formatting_string = "form "
        if raw_data:
            formatting_string += '"Raw"CO2RAWUC"ppm"'
            if with_compensation_data or filtered_data:
                formatting_string += '"; "'
        if with_compensation_data:
            formatting_string += '"Comp"CO2RAW"ppm"'
            if filtered_data:
                formatting_string += '"; "'
        if filtered_data:
            formatting_string += '"Filt"CO2"ppm"'
        formatting_string += "#r#n"

        RS232.write(f"\x1B {formatting_string}\r\n".encode("utf-8"))
        RS232.write(f"\x1B echo {'on' if echo else 'off'}\r\n".encode("utf-8"))

        if save_eeprom:
            RS232.write("save\r\n".encode("utf-8"))
        RS232.flush()
        time.sleep(1)

    @staticmethod
    def get_info(
        device_info=True, software_version=False, errors=False, corrections=False
    ):
        """Send diffrent information about the versions and settings of the CO2 sensor
        device_info shows name/software version, serien number, last calibration,
            measurment span, pressure, humidity, oxygen, compensations, interface
        software_version shows software version (also in device_info)
        errors shows the error messages that are received
        corrections shows the last linear and multipoint correction value
        return: string of the complete answer of the CO2 sensor
        """
        GMP343._receive_serial_cache(False)

        if device_info:
            RS232.write("??\r\n".encode("utf-8"))
        if software_version:
            RS232.write("vers\r\n".encode("utf-8"))
        if errors:
            RS232.write("errs\r\n".encode("utf-8"))
        if corrections:
            RS232.write("corr\r\n".encode("utf-8"))

        RS232.flush()
        time.sleep(1)

        received_serial_cache = GMP343._receive_serial_cache(True)

        return received_serial_cache.decode("cp1252")

    def _receive_serial_cache(thread_receiving_data: bool):
        """Internal class function that can stop or start the receiving data
        in the deamon thread. Also empty the serial cache and returns the bytearray
        """
        if not thread_receiving_data:
            GMP343.thread_receiving_data = thread_receiving_data
            time.sleep(0.05)  # max runtime of one cycle in receiving data loop

        received_serial_cache = bytearray(0)
        while RS232.inWaiting() > 0:
            received_serial_cache = RS232.read(RS232.inWaiting())

        if thread_receiving_data:
            # stop/start the deamon thread until the return value
            GMP343.thread_receiving_data = thread_receiving_data
            time.sleep(0.05)  # max runtime of one cycle in receiving data loop

        return received_serial_cache
