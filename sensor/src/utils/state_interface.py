import json
import os
import time

from src import custom_types, utils

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
STATE_PATH = os.path.join(PROJECT_DIR, "config", "state.json")


class StateInterface:
    @staticmethod
    def init() -> None:
        """create state file if it does not exist yet,
        add upgrade time if missing"""

        state = StateInterface.read()
        if state.last_upgrade_time is None:
            state.last_upgrade_time = time.time()

        StateInterface.write(state)

    @staticmethod
    def read() -> custom_types.State:
        logger = utils.Logger("state-interface")
        try:
            with open(STATE_PATH, "r") as f:
                return custom_types.State(**json.load(f))
        except FileNotFoundError:
            logger.warning("state.json is missing, creating a new one")
        except Exception as e:
            logger.warning(f"state.json is invalid, creating a new one: {e}")

        new_empty_state = custom_types.State(
            last_upgrade_time=None,
            last_calibration_time=None,
            current_config_revision=0,
            offline_since=None,
            next_calibration_cylinder=0,
        )
        StateInterface.write(new_empty_state)
        return new_empty_state

    @staticmethod
    def write(new_state: custom_types.State) -> None:
        with open(STATE_PATH, "w") as f:
            json.dump(new_state.dict(), f)
