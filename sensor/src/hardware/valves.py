import time
from typing import Literal
from src import utils, custom_types
import gpiozero

VALVE_PIN_1_OUT = 25
VALVE_PIN_2_OUT = 24
VALVE_PIN_3_OUT = 23
VALVE_PIN_4_OUT = 22


class ValveInterface:
    def __init__(self, config: custom_types.Config) -> None:
        self.logger, self.config = utils.Logger("valves"), config
        self.logger.info("Starting initialization")

        # set up valve control pin connections
        self.pin_factory = utils.get_gpio_pin_factory()
        self.valves: dict[Literal[1, 2, 3, 4], gpiozero.OutputDevice] = {
            1: gpiozero.OutputDevice(
                VALVE_PIN_1_OUT,
                active_high=False,
                initial_value=True,
                pin_factory=self.pin_factory,
            ),
            2: gpiozero.OutputDevice(
                VALVE_PIN_2_OUT,
                active_high=True,
                initial_value=False,
                pin_factory=self.pin_factory,
            ),
            3: gpiozero.OutputDevice(
                VALVE_PIN_3_OUT,
                active_high=True,
                initial_value=False,
                pin_factory=self.pin_factory,
            ),
            4: gpiozero.OutputDevice(
                VALVE_PIN_4_OUT,
                active_high=True,
                initial_value=False,
                pin_factory=self.pin_factory,
            ),
        }
        self.active_input: Literal[1, 2, 3, 4] = 1
        self.set_active_input(1)

        self.logger.info("Finished initialization")

    def set_active_input(self, no: Literal[1, 2, 3, 4]) -> None:
        """first opens the new valve, then closes the old valve"""
        self.valves[no].on()
        time.sleep(0.02)
        self.valves[self.active_input].off()
        self.active_input = no
        self.logger.info(f"switched to valve {no}")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        self.set_active_input(1)
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sur
        for pin in [VALVE_PIN_1_OUT, VALVE_PIN_2_OUT, VALVE_PIN_3_OUT, VALVE_PIN_4_OUT]:
            utils.run_shell_command(f"pigs w {pin} 0")
