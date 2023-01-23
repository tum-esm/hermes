from typing import Literal
from src import utils, custom_types
from src.utils import Constants
import gpiozero


class ValveInterface:
    def __init__(self, config: custom_types.Config) -> None:
        self.logger, self.config = utils.Logger("valves"), config
        self.logger.info("Starting initialization")

        # set up valve control pin connections
        self.pin_factory = utils.gpio.get_pin_factory()
        self.valves: dict[Literal[1, 2, 3, 4], gpiozero.OutputDevice] = {
            1: gpiozero.OutputDevice(
                Constants.Valves.pin_1_out,
                active_high=False,
                initial_value=True,
                pin_factory=self.pin_factory,
            ),
            2: gpiozero.OutputDevice(
                Constants.Valves.pin_2_out,
                active_high=True,
                initial_value=False,
                pin_factory=self.pin_factory,
            ),
            3: gpiozero.OutputDevice(
                Constants.Valves.pin_3_out,
                active_high=True,
                initial_value=False,
                pin_factory=self.pin_factory,
            ),
            4: gpiozero.OutputDevice(
                Constants.Valves.pin_4_out,
                active_high=True,
                initial_value=False,
                pin_factory=self.pin_factory,
            ),
        }
        self.active_input: Literal[1, 2, 3, 4] = 1
        self.set_active_input(1)

        self.logger.info("Finished initialization")

    def set_active_input(self, no: Literal[1, 2, 3, 4]) -> None:
        for number, device in self.valves.items():
            if number == no:
                device.on()
            else:
                device.off()

        self.active_input = no
        self.logger.info(f"switching to valve {no}")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.set_active_input(1)
        self.pin_factory.close()
