import time


def timestamp() -> int:
    """Return current UTC time as unixtime integer."""
    return int(time.time())
