from src import utils


class USBPortInterface:
    """This interface is used to toggle the power of all USB
    ports in case the Arduino or the LTE hat behave weird"""

    @staticmethod
    def toggle_usb_power() -> None:
        """turn off the power on all USB ports, wait 5 seconds,
        turn it on again."""

        logger = utils.Logger("usb-port-interface")

        logger.info("performing power toggle")

        logger.debug("toggling USB hub 1")
        utils.run_shell_command("sudo uhubctl -a cycle -p 1 -d 5")

        logger.debug("toggling USB hub 2")
        utils.run_shell_command("sudo uhubctl -a cycle -p 1 -d 5")

        logger.debug("power toggle successful")
