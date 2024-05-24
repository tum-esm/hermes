import json
import os
import pathlib

from src import custom_types

PROJECT_DIR = pathlib.Path(os.path.abspath(__file__)).parents[2]
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")


class ConfigInterface:
    class FileIsMissing(Exception):
        """raised when config.json was not found"""

    class FileIsInvalid(Exception):
        """raised when config.json is not in a valid format"""

    @staticmethod
    def read() -> custom_types.Config:
        try:
            with open(CONFIG_PATH, "r") as f:
                return custom_types.Config(**json.load(f))
        except FileNotFoundError:
            raise ConfigInterface.FileIsMissing()
        except json.JSONDecodeError:
            raise ConfigInterface.FileIsInvalid("file not in a valid json format")
        except Exception as e:
            raise ConfigInterface.FileIsInvalid(e.args[0])
