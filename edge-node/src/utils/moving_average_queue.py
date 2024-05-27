from typing import Any, Optional


# TODO: improve typing once sum(list()) is easier to describe


class RingBuffer:
    """Appends float values in a ring buffer and returns the average of it"""

    def __init__(self, size: int):
        assert size > 0
        self.size = size
        self.ring_buffer: list[Any] = []

    def append(self, value: Optional[float]) -> None:
        if value is not None:
            if len(self.ring_buffer) < self.size:
                self.ring_buffer.append(value)
            if len(self.ring_buffer) == self.size:
                self.ring_buffer = self.ring_buffer[1:]
                self.ring_buffer.append(value)
                assert len(self.ring_buffer) == self.size

    def avg(self) -> Any:
        if len(self.ring_buffer) > 0:
            value = sum(self.ring_buffer) / len(self.ring_buffer)
            return round(value, 2)
        else:
            return None

    def clear(self) -> None:
        self.ring_buffer = []
