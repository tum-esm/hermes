from typing import Any
from src import types


class MQTTInterface:
    @staticmethod
    def get_messages(config: types.ConfigDict) -> list[Any]:
        return []
