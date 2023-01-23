import json
import os
from src import custom_types, utils

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
STATE_PATH = os.path.join(PROJECT_DIR, "config", "state.json")


class StateInterface:
    @staticmethod
    def read() -> custom_types.State:
        logger = utils.Logger("state-interface")
        try:
            with open(STATE_PATH, "r") as f:
                return custom_types.State(**json.load(f))
        except FileNotFoundError:
            logger.warning("state.json is missing")
        except Exception as e:
            logger.warning(f"state.json is invalid: {e}")

        new_empty_state = custom_types.State(
            last_upgrade_time=None,
            last_calibration_time=None,
        )
        StateInterface.dump(new_empty_state)
        return new_empty_state

    @staticmethod
    def write(new_state: custom_types.State) -> None:
        with open(STATE_PATH, "w") as f:
            json.dump(new_state.dict(), f)
