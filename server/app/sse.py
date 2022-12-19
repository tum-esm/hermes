import json


class ServerSentEvent:
    def __init__(self, data: dict):
        self.data = data

    def encode(self):
        return f"data: {json.dumps(self.data)}\n\n"
