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
        mainboard_sensor_data = self.hardware_interface.mainboard_sensor.get_data()
        cpu_temperature = utils.get_cpu_temperature()
        self.logger.debug(
            f"mainboard temp. = {mainboard_sensor_data.temperature} °C, "
            + f"raspi cpu temp. = {cpu_temperature} °C"
        )
        self.logger.debug(
            f"enclosure humidity = {mainboard_sensor_data.humidity} % rH, "
            + f"enclosure pressure = {mainboard_sensor_data.pressure} hPa"
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
                        mainboard_temperature=mainboard_sensor_data.temperature,
                        cpu_temperature=cpu_temperature,
                        enclosure_humidity=mainboard_sensor_data.humidity,
                        enclosure_pressure=mainboard_sensor_data.pressure,
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
