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
        # enclosure and mainboard temperature (controls)
        self.heated_enclosure = HeatedEnclosureInterface(config)
        self.mainboard_sensor = MainboardSensorInterface(config)

        # measurement sensors
        self.air_inlet_sensor = AirInletSensorInterface()
        self.co2_sensor = CO2SensorInterface(config)
        self.wind_sensor = WindSensorInterface(config)

        # measurement actors
        self.pump = PumpInterface(config)
        self.valve = ValveInterface(config)

        # other
        self.ups = UPSInterface(config)

    # TODO: move teardowns in here
    # TODO: move check_errors in here
