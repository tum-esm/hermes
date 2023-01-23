import json
import os
from src import custom_types

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
STATE_PATH = os.path.join(PROJECT_DIR, "config", "state.json")


class StateInterface:
    class FileIsMissing(Exception):
        """raised when state.json was not found"""

    class FileIsInvalid(Exception):
        """raised when state.json is not in a valid format"""

    @staticmethod
    def read() -> custom_types.State:
        try:
            with open(STATE_PATH, "r") as f:
                return custom_types.State(**json.load(f))
        except FileNotFoundError:
            raise StateInterface.FileIsMissing()
        except json.JSONDecodeError:
            raise StateInterface.FileIsInvalid("file not in a valid json format")
        except Exception as e:
            raise StateInterface.FileIsInvalid(e.args[0])
