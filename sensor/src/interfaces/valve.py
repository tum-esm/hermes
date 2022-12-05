from typing import Literal
from src import utils, custom_types
from src.utils import Constants
import gpiozero


class ValveInterface:
    def __init__(self, config: custom_types.Config) -> None:
        self.config = config
        self.logger = utils.Logger(config, "valves")
        self.set_active_input(1)

        self.valves: dict[Literal[1, 2, 3, 4], gpiozero.OutputDevice] = {
            1: gpiozero.OutputDevice(
                Constants.valves.pin_1_out, active_high=False, initial_value=True
            ),
            2: gpiozero.OutputDevice(
                Constants.valves.pin_2_out, active_high=True, initial_value=False
            ),
            3: gpiozero.OutputDevice(
                Constants.valves.pin_3_out, active_high=True, initial_value=False
            ),
            4: gpiozero.OutputDevice(
                Constants.valves.pin_4_out, active_high=True, initial_value=False
            ),
        }

    def set_active_input(self, no: Literal[1, 2, 3, 4], logger: bool = True) -> None:
        for number, device in self.valves.items():
            if number == no:
                device.on()
            else:
                device.off()

        message = f"switching to valve {no}"
        if logger:
            self.logger.info(message)
        else:
            print(message)
