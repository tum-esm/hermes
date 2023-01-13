import time
from typing import Optional
from src import utils, custom_types
import re

number_regex = r"\d+(\.\d+)?"
measurement_pattern = re.compile(
    f"version: {number_regex}; target: {number_regex}; allowed "
    + f"deviation: {number_regex}; measured: {number_regex};"
)
relais_status_pattern = re.compile(r"heater: (on|off); fan: (on|off)")


class HeatedEnclosureInterface:
    class DeviceFailure(Exception):
        """raised when the arduino either didn't answer for a while
        or when the code could not be uploaded to the device"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="heated-enclosure")
        self.config = config

        # TODO: flash software onto device

        self.serial_interface = utils.serial_interfaces.SerialOneDirectionalInterface(
            port=utils.Constants.WindSensor.serial_port,
            baudrate=9600,
        )
        self.measurement: Optional[custom_types.HeatedEnclosureMeasurement] = None
        self.relais_status: Optional[custom_types.HeatedEnclosureRelaisStatus] = None
        self.last_update_time: float = time.time()

    def _update_current_values(self) -> None:
        new_messages = self.rs232_interface.get_messages()
        now = round(time.time())
        for message in new_messages:
            if measurement_pattern.match(message) is not None:
                # determine the software currently used by the arduino
                # raise exception if software us too old
                used_software_version = message.split(";")[0].replace("version: ", "")
                if used_software_version != self.config.version:
                    raise HeatedEnclosureInterface.DeviceFailure(
                        f"Not running the expected software version. "
                        + f"Device uses {used_software_version}"
                    )
                parsed_message = "".join(
                    float(c)
                    for c in message[len(used_software_version) + 11 :]
                    if c.isnumeric() or c in [";", "."]
                )
                t, ad, m = parsed_message.split(",")
                self.measurement = custom_types.HeatedEnclosureMeasurement(
                    target=t, allowed_deviation=ad, measured=m
                )
                self.last_update_time = now
            if relais_status_pattern.match(message) is not None:
                self.device_status = custom_types.HeatedEnclosureRelaisStatus(
                    heater_is_on=("heater: on" in message),
                    fan_is_on=("fan: on" in message),
                )
                self.last_update_time = now

    def get_current_measurement(self) -> Optional[custom_types.WindSensorData]:
        self._update_current_values()
        return self.measurement

    def get_current_relais_status(self) -> Optional[custom_types.WindSensorStatus]:
        self._update_current_values()
        return self.relais_status
