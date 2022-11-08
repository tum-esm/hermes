import RPi.GPIO as GPIO
import time
from src import utils, types
from src.utils import Constants

GPIO.setup(Constants.ups.pin_ready_in, GPIO.IN)
GPIO.setup(Constants.ups.pin_battery_mode_in, GPIO.IN)
GPIO.setup(Constants.ups.pin_alarm_in, GPIO.IN)


class UPSInterface:
    def __init__():
        # Interrupt-Event
        GPIO.add_event_detect(
            Constants.ups.pin_ready_in,
            GPIO.BOTH,
            callback=UPSInterface.STATUS_READY_Interrupt,
            bouncetime=300,
        )
        GPIO.add_event_detect(
            Constants.ups.pin_battery_mode_in,
            GPIO.BOTH,
            callback=UPSInterface.STATUS_BAT_MODE_Interrupt,
            bouncetime=300,
        )
        GPIO.add_event_detect(
            Constants.ups.pin_alarm_in,
            GPIO.BOTH,
            callback=UPSInterface.STATUS_ALARM_Interrupt,
            bouncetime=300,
        )

        UPSInterface._interrupt_callback_ready(Constants.ups.pin_ready_in)
        UPSInterface._interrupt_callback_battery_mode(Constants.ups.pin_battery_mode_in)
        UPSInterface._interrupt_callback_alarm(Constants.ups.pin_alarm_in)

    @staticmethod
    def _battery_is_ready() -> bool:
        """The pin goes high if the battery of the UPS is finished loading and
        when the battery voltage is below the threshold set in the UPS software."""
        return GPIO.input(Constants.ups.pin_ready_in) == 1

    @staticmethod
    def _battery_is_active() -> bool:
        """The pin goes high if the system is powered by the UPS battery."""
        return GPIO.input(Constants.ups.pin_battery_mode_in) == 1

    @staticmethod
    def _battery_alarm_is_set() -> bool:
        """The pin goes high if the battery has any error or has been disconected."""
        return GPIO.input(Constants.ups.pin_alarm_in) == 1

    # Interrupt Callback-Funktion
    @staticmethod
    def _interrupt_callback_ready(input_pin: int) -> None:
        """Called when battery_is_ready() changes"""
        if UPSInterface.battery_is_ready() and UPSInterface.battery_is_active():
            time.sleep(1)  # Need to confirm that the battery wasn't fully charged
            if UPSInterface.battery_is_active():
                # StateInterface.update({"Shut down": True})
                # logger.error(
                #    "UPS battery voltage is under threshold - Shutting down"
                # )
                pass

        elif GPIO.input(Constants.ups.pin_ready_in):
            pass
            # StateInterface.update({"UPS_STATUS_READY": True})
            # logger.system_data_logger.info("UPS battery is fully charged")

        else:
            pass
            # StateInterface.update({"UPS_STATUS_READY": False})
            # logger.system_data_logger.info("UPS battery is not fully charged")

        # print("UPS Status Ready: ", GPIO.input(UPS_STATUS_READY))

    @staticmethod
    def _interrupt_callback_battery_mode(input_pin: int) -> None:
        """Called when battery_is_active() changes"""
        if GPIO.input(Constants.ups.pin_battery_mode_in):
            pass
            # StateInterface.update({"UPS_STATUS_BAT_MODE": True})
            # logger.system_data_logger.warning("System is powered by the battery")
        else:
            pass
            # StateInterface.update({"UPS_STATUS_BAT_MODE": False})
            # logger.system_data_logger.info("System is powered external")

        # print("UPS Status Bat.-Mode: ", GPIO.input(UPS_STATUS_BAT_MODE))

    @staticmethod
    def _interrupt_callback_alarm(input_pin: int) -> None:
        """Called when battery_alarm_is_set() changes"""
        if GPIO.input(Constants.ups.pin_alarm_in):
            pass
            # StateInterface.update({"UPS_STATUS_ALARM": True})
            # logger.system_data_logger.warning("Battery error detected")
        else:
            pass
            # StateInterface.update({"UPS_STATUS_ALARM": False})
            # logger.system_data_logger.info("Battery status ok")

        # print("UPS Status Alarm: ", GPIO.input(UPS_STATUS_ALARM))
