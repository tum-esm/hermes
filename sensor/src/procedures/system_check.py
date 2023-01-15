import psutil
from src import hardware_interfaces, custom_types, utils


class SystemCheckProcedure:
    """runs every mainloop call"""

    def __init__(self, config: custom_types.Config) -> None:
        self.logger = utils.Logger(origin="system-checks")
        self.config = config
        self.mainboard_sensor = hardware_interfaces.MainboardSensorInterface()
        self.heated_enclosure = hardware_interfaces.HeatedEnclosureInterface()

    def run(self) -> None:
        # evaluate system ambient conditions
        system_data = self.mainboard_sensor.get_system_data()
        self.logger.debug(
            f"mainboard temp. = {system_data.mainboard_temperature} °C, "
            + f"raspi cpu temp. = {system_data.cpu_temperature} °C"
        )
        self.logger.debug(
            f"enclosure humidity = {system_data.enclosure_humidity} % rH, "
            + f"enclosure pressure = {system_data.enclosure_pressure} hPa"
        )
        self.mainboard_sensor.check_errors()

        # interact with heated enclosure
        heated_enclosure_data = self.heated_enclosure.get_current_data()
        if heated_enclosure_data is not None:
            self.logger.debug(
                f"heated enclosure temperature = {heated_enclosure_data.measured} °C, "
                + f"heated enclosure heater = is {'on' if heated_enclosure_data.heater_is_on else 'off'}, "
                + f"heated enclosure fan = is {'on' if heated_enclosure_data.fan_is_on else 'off'}"
            )
            # TODO: send heated enclosure data via MQTT
        self.heated_enclosure.check_errors()

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

        # mqtt sending loop
        utils.SendingMQTTClient.check_errors()
        utils.SendingMQTTClient.log_statistics()
