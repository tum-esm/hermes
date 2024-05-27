import time
from typing import Optional

import gpiozero

from src import utils, custom_types

UPS_READY_PIN_IN = 5
UPS_BATTERY_MODE_PIN_IN = 10
UPS_ALARM_PIN_IN = 7


class UPSInterface:
    def __init__(
        self,
        config: custom_types.Config,
        testing: bool = False,
        simulate: bool = False,
    ):
        self.logger = utils.Logger(
            origin="ups",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.config = config
        self.simulate = simulate

        self.logger.info("Starting initialization")

        self.powered_by_grid: Optional[bool] = None
        self.battery_is_fully_charged: Optional[bool] = None
        self.battery_error_detected: Optional[bool] = None
        self.battery_above_voltage_threshold: Optional[bool] = None

        if simulate:
            self.logger.info("Simulating UPS.")
            return

        # use underlying pigpio library
        self.pin_factory = utils.get_gpio_pin_factory()

        self.logger.info("Finished initialization")

    def _read_power_mode(self) -> None:
        """
        UPS_BATTERY_MODE_PIN_IN is HIGH when the system is powered by the battery
        UPS_BATTERY_MODE_PIN_IN is LOW when the system is powered by the grid
        """

        if self.simulate:
            self.logger.info("simulating power mode 'grid'")
            self.powered_by_grid = True
            return

        power_mode = gpiozero.DigitalInputDevice(
            UPS_BATTERY_MODE_PIN_IN,
            bounce_time=0.3,
            pin_factory=self.pin_factory,
        )

        if not power_mode.is_active:
            self.logger.info("system is powered by the grid")
            self.powered_by_grid = True
        else:
            self.logger.info("system is powered by the battery")
            self.powered_by_grid = False

    def _read_battery_state(self) -> None:
        """
        UPS_STATUS_READY is HIGH when the battery is fully charged
        UPS_STATUS_READY is LOW when the battery is not fully charged
        (UPS_STATUS_READY is HIGH & UPS_BATTERY_MODE_PIN_IN is HIGH)
        when the system is powered by the system and the battery voltage
        has dropped to a minimum
        """

        if self.simulate:
            self.logger.info("simulating battery state 'fully charged'")
            self.battery_is_fully_charged = True
            return

        battery_state = gpiozero.DigitalInputDevice(
            UPS_READY_PIN_IN, bounce_time=0.3, pin_factory=self.pin_factory
        )

        power_mode = gpiozero.DigitalInputDevice(
            UPS_BATTERY_MODE_PIN_IN,
            bounce_time=0.3,
            pin_factory=self.pin_factory,
        )

        if battery_state.is_active:
            self.logger.info("the battery is fully charged")
            self.battery_is_fully_charged = True
        else:
            self.logger.info("the battery is not fully charged")
            self.battery_is_fully_charged = False

        # this is probably never reached as the power is shut down in this case
        if battery_state.is_active & power_mode.is_active:
            self.logger.info(
                "the battery voltage has dropped below the minimum threshold"
            )
            self.battery_above_voltage_threshold = False
        else:
            self.logger.info("the battery voltage is above the minimum threshold")
            self.battery_above_voltage_threshold = True

    def _read_alarm_state(self) -> None:
        """
        UPS_ALARM_PIN_IN is HIGH when a battery error is detected
        UPS_ALARM_PIN_IN is LOW when the battery status is okay
        """

        if self.simulate:
            self.logger.info("simulating battery error 'False'")
            self.battery_error_detected = False
            return

        alarm_state = gpiozero.DigitalInputDevice(
            UPS_ALARM_PIN_IN, bounce_time=0.3, pin_factory=self.pin_factory
        )

        if not alarm_state.is_active:
            self.logger.info("the battery status is fine")
            self.battery_error_detected = False
        else:
            self.logger.info("a battery error was detected")
            self.battery_error_detected = True

    def update_ups_status(self) -> None:
        try:
            self._read_power_mode()
            self._read_battery_state()
            self._read_alarm_state()
        except Exception:
            # retry
            self.pin_factory = utils.get_gpio_pin_factory()
            time.sleep(1)
            self._read_power_mode()
            self._read_battery_state()
            self._read_alarm_state()

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        if self.simulate:
            return

        self.pin_factory.close()
