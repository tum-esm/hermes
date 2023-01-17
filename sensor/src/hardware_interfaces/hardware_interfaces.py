from typing import Optional
import smbus2
import bme280
import os
from src import utils, custom_types
from src.hardware_interfaces import (
    AirInletSensorInterface,
    CO2SensorInterface,
    HeatedEnclosureInterface,
    MainboardSensorInterface,
    PumpInterface,
    UPSInterface,
    ValveInterface,
    WindSensorInterface,
)


class HardwareInterfaces:
    def __init__(self, config: custom_types.Config) -> None:
        # measurement sensors
        self.air_inlet_sensor = AirInletSensorInterface()
        self.co2_sensor = CO2SensorInterface(config)
        self.wind_sensor = WindSensorInterface(config)

        # measurement actors
        self.pump = PumpInterface(config)
        self.valves = ValveInterface(config)

        # enclosure controls
        self.heated_enclosure = HeatedEnclosureInterface(config)
        self.mainboard_sensor = MainboardSensorInterface(config)
        self.ups = UPSInterface(config)

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.air_inlet_sensor.teardown()
        self.co2_sensor.teardown()
        self.wind_sensor.teardown()
        self.pump.teardown()
        self.valves.teardown()
        self.heated_enclosure.teardown()
        self.mainboard_sensor.teardown()
        self.ups.teardown()

    # TODO: move check_errors in here
