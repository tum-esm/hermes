from src import utils, custom_types
from src.utils import Constants
import gpiozero


class UPSInterface:
    def __init__(self, config: custom_types.Config):
        logger = utils.Logger("ups")
        self.pin_factory = utils.gpio.get_pin_factory()

        # pin goes high if the system is powered by the UPS battery
        mode_input = gpiozero.DigitalInputDevice(
            Constants.UPS.battery_mode_pin_in,
            bounce_time=300,
            pin_factory=self.pin_factory,
        )
        mode_input.when_activated = lambda: logger.warning(
            "system is powered by battery", config=config
        )
        mode_input.when_deactivated = lambda: logger.info(
            "system is powered externally"
        )

        # pin goes high if the battery has any error or has been disconected
        alarm_input = gpiozero.DigitalInputDevice(
            Constants.UPS.alarm_pin_in, bounce_time=300, pin_factory=self.pin_factory
        )
        alarm_input.when_activated = lambda: logger.warning(
            "battery error detected", config=config
        )
        alarm_input.when_deactivated = lambda: logger.info("battery status is ok")

        def _on_battery_is_ready() -> None:
            if mode_input.is_active:
                logger.error("battery voltage is under threshold", config=config)
                # TODO: https://github.com/tum-esm/insert-name-here/issues/33
            else:
                logger.info("battery is fully charged")

        # pin goes high if the battery is empty or fully charged (two thresholds like 10% and 90%)
        ready_input = gpiozero.DigitalInputDevice(
            Constants.UPS.ready_pin_in, bounce_time=2000, pin_factory=self.pin_factory
        )
        ready_input.when_activated = _on_battery_is_ready

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.pin_factory.close()
