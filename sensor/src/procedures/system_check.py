import time
import psutil
from src import hardware, custom_types, utils
from .messaging_agent import MessagingAgent


class SystemCheckProcedure:
    """runs every mainloop call"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="system-check-procedure"), config
        self.hardware_interface = hardware_interface
        self.active_mqtt_queue = utils.ActiveMQTTQueue()

    def run(self) -> None:
        # evaluate system ambient conditions
        system_data = self.hardware_interface.mainboard_sensor.get_system_data()
        self.logger.debug(
            f"mainboard temp. = {system_data.mainboard_temperature} °C, "
            + f"raspi cpu temp. = {system_data.cpu_temperature} °C"
        )
        self.logger.debug(
            f"enclosure humidity = {system_data.enclosure_humidity} % rH, "
            + f"enclosure pressure = {system_data.enclosure_pressure} hPa"
        )

        # evaluate disk usage
        disk_usage = psutil.disk_usage("/")
        self.logger.debug(
            f"{round(disk_usage.used/1_000_000)}/{round(disk_usage.total/1_000_000)} "
            + f"MB disk space used (= {disk_usage.percent} %)"
        )
        if disk_usage.percent > 80:
            self.logger.warning(
                f"disk space usage is very high ({disk_usage.percent} %)",
                config=self.config,
            )

        # evaluate CPU usage
        cpu_usage_percent = psutil.cpu_percent()
        self.logger.debug(f"{cpu_usage_percent} % total CPU usage")
        if cpu_usage_percent > 90:
            self.logger.warning(
                f"CPU usage is very high ({cpu_usage_percent} %)", config=self.config
            )

        self.active_mqtt_queue.enqueue_message(
            self.config,
            custom_types.MQTTDataMessageBody(
                revision=self.config.revision,
                timestamp=round(time.time(), 2),
                value=custom_types.MQTTSystemData(
                    variant="system",
                    data=custom_types.SystemData(
                        mainboard_temperature=system_data.mainboard_temperature,
                        cpu_temperature=system_data.cpu_temperature,
                        enclosure_humidity=system_data.enclosure_humidity,
                        enclosure_pressure=system_data.enclosure_pressure,
                        disk_usage=round(disk_usage.percent / 100, 4),
                        cpu_usage=round(cpu_usage_percent / 100, 4),
                    ),
                ),
            ),
        )

        # check for errors
        self.hardware_interface.check_errors()
        if self.config.active_components.mqtt_communication:
            MessagingAgent.check_errors()
