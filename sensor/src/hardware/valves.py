import time
from typing import Literal

import gpiozero

from src import utils, custom_types

VALVE_PIN_1_OUT = 25
VALVE_PIN_2_OUT = 24
VALVE_PIN_3_OUT = 23
VALVE_PIN_4_OUT = 22


class ValveInterface:
    def __init__(
        self,
        config: custom_types.Config,
        testing: bool = False,
        simulate: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            origin="valves",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.config = config
        self.simulate = simulate
        self.logger.info("Starting initialization")

        if self.simulate:
            self.logger.info("Simulating valves.")
            return

        # set up valve control pin connections
        self.pin_factory = utils.get_gpio_pin_factory()
        self.valves: dict[Literal[1, 2, 3, 4], gpiozero.OutputDevice] = {
            1: gpiozero.OutputDevice(VALVE_PIN_1_OUT, pin_factory=self.pin_factory),
            2: gpiozero.OutputDevice(VALVE_PIN_2_OUT, pin_factory=self.pin_factory),
            3: gpiozero.OutputDevice(VALVE_PIN_3_OUT, pin_factory=self.pin_factory),
            4: gpiozero.OutputDevice(VALVE_PIN_4_OUT, pin_factory=self.pin_factory),
        }
        self.active_input: Literal[1, 2, 3, 4] = self.config.measurement.valve_number
        self.logger.info(f"Initialized with switching to valve: {self.active_input}")
        self.set_active_input(self.active_input)

        self.logger.info("Finished initialization")

    def set_active_input(self, no: Literal[1, 2, 3, 4]) -> None:
        """Allows flow through selected valve.
        Permits flow through all other valves.

        Waits shortly after closing input valve 1 before opening calibration valves."""

        if no == 1:
            self.valves[1].off()
            self.valves[2].off()
            self.valves[3].off()
            self.valves[4].off()
        if no == 2:
            self.valves[1].on()
            time.sleep(0.5)
            self.valves[2].on()
            self.valves[3].off()
            self.valves[4].off()
        if no == 3:
            self.valves[1].on()
            time.sleep(0.5)
            self.valves[2].off()
            self.valves[3].on()
            self.valves[4].off()
        if no == 4:
            self.valves[1].on()
            time.sleep(0.5)
            self.valves[2].off()
            self.valves[3].off()
            self.valves[4].on()

        self.active_input = no
        self.logger.info(f"switched to valve {self.active_input}")

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        if self.simulate:
            return

        self.set_active_input(1)
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sur
        for pin in [VALVE_PIN_1_OUT, VALVE_PIN_2_OUT, VALVE_PIN_3_OUT, VALVE_PIN_4_OUT]:
            utils.run_shell_command(f"pigs w {pin} 0")
