from src import utils


# TODO: give uhubctl sudo permissions in the setup script


class USBPortInterface:
    """This interface is used to toggle the power of all USB
    ports in case the Arduino or the LTE hat behave weird"""

    @staticmethod
    def toggle_usb_power(delay: int = 5) -> None:
        """turn off the power on all USB ports, wait n seconds,
        turn it on again."""

        logger = utils.Logger("usb-port-interface")

        logger.info("performing power toggle")

        logger.debug("toggling USB hub 1")
        utils.run_shell_command(f"sudo uhubctl -a cycle -l 1 -d {delay}")

        logger.debug("toggling USB hub 2")
        utils.run_shell_command(f"sudo uhubctl -a cycle -l 2 -d {delay}")

        logger.debug("power toggle successful")
