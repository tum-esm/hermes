import time

import psutil

from src import hardware, custom_types, utils


class SystemCheckProcedure:
    """runs every mainloop call"""

    def __init__(
        self,
        config: custom_types.Config,
        hardware_interface: hardware.HardwareInterface,
        simulate: bool = False,
    ) -> None:
        self.logger, self.config = utils.Logger(origin="system-check-procedure"), config
        self.hardware_interface = hardware_interface
        self.message_queue = utils.MessageQueue()
        self.simulate = simulate

    def run(self) -> None:
        """runs system check procedure

        - log mainboard/CPU temperature
        - log enclosure humidity and pressure
        - check whether mainboard/CPU temperature is above 70°C
        - log CPU/disk/memory usage
        - check whether CPU/disk/memory usage is above 80%
        - send system data via MQTT
        - check hardware interfaces for errors
        - check messaging agent for errors
        """

        mainboard_bme280_data = self.hardware_interface.mainboard_sensor.get_data()
        mainboard_temperature = mainboard_bme280_data.temperature
        cpu_temperature = utils.get_cpu_temperature(self.simulate)
        self.logger.debug(
            f"mainboard temp. = {mainboard_temperature} °C, "
            + f"raspi cpu temp. = {cpu_temperature} °C"
        )
        self.logger.debug(
            f"enclosure humidity = {mainboard_bme280_data.humidity} % rH, "
            + f"enclosure pressure = {mainboard_bme280_data.pressure} hPa"
        )

        if (mainboard_temperature is not None) and (mainboard_temperature > 70):
            self.logger.warning(
                f"mainboard temperature is very high ({mainboard_temperature} °C)",
                config=self.config,
            )

        if (cpu_temperature is not None) and (cpu_temperature > 70):
            self.logger.warning(
                f"CPU temperature is very high ({cpu_temperature} °C)",
                config=self.config,
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
        if cpu_usage_percent > 80:
            self.logger.warning(
                f"CPU usage is very high ({cpu_usage_percent} %)", config=self.config
            )

        memory_usage_percent = psutil.virtual_memory().percent
        self.logger.debug(f"{memory_usage_percent} % total memory usage")
        if memory_usage_percent > 80:
            self.logger.warning(
                f"memory usage is very high ({memory_usage_percent} %)",
                config=self.config,
            )
            
        # read UPS status
        self.hardware_interface.ups.update_ups_status()

        state = utils.StateInterface.read()

        self.message_queue.enqueue_message(
            self.config,
            custom_types.MQTTMeasurementMessageBody(
                revision=state.current_config_revision,
                timestamp=round(time.time(), 2),
                value=custom_types.MQTTSystemData(
                    enclosure_bme280_temperature=mainboard_temperature,
                    enclosure_bme280_humidity=mainboard_bme280_data.humidity,
                    enclosure_bme280_pressure=mainboard_bme280_data.pressure,
                    raspi_cpu_temperature=cpu_temperature,
                    raspi_disk_usage=round(disk_usage.percent / 100, 4),
                    raspi_cpu_usage=round(cpu_usage_percent / 100, 4),
                    raspi_memory_usage=round(memory_usage_percent / 100, 4),
                    ups_powered_by_grid=1.0 if self.hardware_interface.ups.powered_by_grid else 0.0,
                    ups_battery_is_fully_charged=1.0 if self.hardware_interface.ups.battery_is_fully_charged else 0.0,
                    ups_battery_error_detected=1.0 if self.hardware_interface.ups.battery_error_detected else 0.0,
                    ups_battery_above_voltage_threshold=1.0 if self.hardware_interface.ups.battery_above_voltage_threshold else 0.0,
                ),
            ),
        )

        # check for errors
        self.hardware_interface.check_errors()
