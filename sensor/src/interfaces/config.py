import json
import os
import pathlib
from src import types

PROJECT_DIR = pathlib.Path(os.path.abspath(__file__)).parents[2]
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")


class ConfigInterface:
    class FileIsMissing(Exception):
        """raised when config.json was not found"""

    class FileIsInvalid(Exception):
        """raised when config.json is not in a valid format"""

    @staticmethod
    def read() -> types.ConfigDict:
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                types.validate_config_dict(config)
                validated_config: types.ConfigDict = config
        except FileNotFoundError:
            raise ConfigInterface.FileIsMissing()
        except json.JSONDecodeError:
            raise ConfigInterface.FileIsInvalid("file not in a valid json format")
        except Exception as e:
            raise ConfigInterface.FileIsInvalid(e.args[0])

        return validated_config
