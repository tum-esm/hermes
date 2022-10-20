import json
import os
from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")


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
            raise ConfigInterface.FileIsInvalid(e)

        return validated_config
