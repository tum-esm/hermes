from src import utils, types
from src.utils import Constants
import gpiozero


class UPSInterface:
    def __init__(self, config: types.Config):
        logger = utils.Logger(config, "ups")

        # pin goes high if the system is powered by the UPS battery
        mode_input = gpiozero.DigitalInputDevice(Constants.ups.battery_mode_pin_in, bounce_time=300)
        mode_input.when_activated = lambda: logger.warning("system is powered by battery")
        mode_input.when_deactivated = lambda: logger.info("system is powered externally")

        # pin goes high if the battery has any error or has been disconected
        alarm_input = gpiozero.DigitalInputDevice(Constants.ups.alarm_pin_in, bounce_time=300)
        alarm_input.when_activated = lambda: logger.warning("battery error detected")
        alarm_input.when_deactivated = lambda: logger.info("battery status is ok")

        def _on_battery_is_ready() -> None:
            if mode_input.is_active:
                logger.error("battery voltage is under threshold")
            else:
                logger.info("battery is fully charged")

        # pin goes high if the battery is empty or fully charged (two thresholds like 10% and 90%)
        ready_input = gpiozero.DigitalInputDevice(Constants.ups.ready_pin_in, bounce_time=2000)
        ready_input.when_activated = _on_battery_is_ready
