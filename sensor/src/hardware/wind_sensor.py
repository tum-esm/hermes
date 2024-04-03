import random
import re
import time
from typing import Optional, Tuple

import gpiozero
import gpiozero.pins.pigpio

from src import utils, custom_types

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
        simulate: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            origin="wind-sensor",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.config = config
        self.simulate = simulate

        self.logger.info("Starting initialization")
        self.wind_measurement: Optional[custom_types.WindSensorData] = None
        self.device_status: Optional[custom_types.WindSensorStatus] = None

        if self.simulate:
            self.logger.info("Simulating wind sensor.")
            return

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
            line_ending="\r\n",
        )

        self.logger.info("Finished initialization")

    def _update_current_values(self) -> None:
        start_time = time.time()
        new_messages = []

        while True:
            answer = self.wxt532_interface.get_messages()
            if not answer:
                break
            if (time.time() - start_time) > 5:
                break

            time.sleep(0.05)

            new_messages += answer

        now = round(time.time())
        wind_measurements: list[custom_types.WindSensorData] = []

        for message in new_messages:
            # Check if there's a match for the measurement_pattern
            measurement_match = re.search(measurement_pattern, message)
            if measurement_match is not None:
                # Extract the values using group() method
                measurement_message = custom_types.WindSensorData(
                    direction_min=measurement_match.group(1),
                    direction_avg=measurement_match.group(2),
                    direction_max=measurement_match.group(3),
                    speed_min=measurement_match.group(4),
                    speed_avg=measurement_match.group(5),
                    speed_max=measurement_match.group(6),
                    last_update_time=now,
                )
                wind_measurements.append(measurement_message)

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

        # min/max/average over all received messages
        if len(wind_measurements) > 0:
            self.logger.info(
                f"Processed {len(wind_measurements)} wind sensor measurements during the last "
                f"{self.config.measurement.procedure_seconds} seconds interval."
            )
            self.wind_measurement = custom_types.WindSensorData(
                direction_min=min([m.direction_min for m in wind_measurements]),
                direction_avg=utils.functions.avg_list(
                    [m.direction_avg for m in wind_measurements], 1
                ),
                direction_max=max([m.direction_max for m in wind_measurements]),
                speed_min=min([m.speed_min for m in wind_measurements]),
                speed_avg=utils.functions.avg_list(
                    [m.speed_avg for m in wind_measurements], 1
                ),
                speed_max=max([m.speed_max for m in wind_measurements]),
                last_update_time=[m.last_update_time for m in wind_measurements][-1],
            )
        else:
            self.wind_measurement = None

    def get_current_sensor_measurement(
        self,
    ) -> Tuple[
        Optional[custom_types.WindSensorData],
        Optional[custom_types.WindSensorStatus],
    ]:
        if self.simulate:
            wind_dir = 60 + random.random()*120
            wind_speed = 3 + random.random()*8
            return (
                custom_types.WindSensorData(
                    # generate random wind data
                    direction_min=wind_dir - 30,
                    direction_avg=wind_dir,
                    direction_max=wind_dir + 30,
                    speed_min=wind_speed-3,
                    speed_avg=wind_speed,
                    speed_max=wind_speed+3,
                    last_update_time=round(time.time()),
                ),
                custom_types.WindSensorStatus(
                    # generate random device status
                    temperature=20 + random.random()*10,
                    heating_voltage=24 + random.random()*2,
                    supply_voltage=24 + random.random()*2,
                    reference_voltage=3.6 + random.random()*0.4,
                    last_update_time=round(time.time()),
                ),
            )
        self._update_current_values()
        return self.wind_measurement, self.device_status

    def check_errors(self) -> None:
        """checks whether the wind sensor behaves incorrectly - Possibly
        raises the WindSensorInterface.DeviceFailure exception"""

        now = time.time()

        if self.device_status is not None:
            # only consider values less than 5 minutes old
            if (now - self.device_status.last_update_time) < 300:
                if self.simulate:
                    self.logger.info("the wind sensor check doesn't report any errors")
                    return

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
        if self.simulate:
            return
        
        self.power_pin.off()
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {WIND_SENSOR_POWER_PIN_OUT} 0")
