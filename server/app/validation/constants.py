import enum


class Limit(int, enum.Enum):
    SMALL = 2**6  # 64
    MEDIUM = 2**8  # 256
    LARGE = 2**10  # 1024
    MAXINT4 = 2**31  # Maximum value signed 32-bit integer + 1


class Pattern(str, enum.Enum):
    SENSOR_IDENTIFIER = r"^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$"
    VALUE_IDENTIFIER = r"^(?!_)(?!.*__)[a-z0-9_]{1,64}(?<!_)$"
