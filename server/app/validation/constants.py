import enum


class Limit(int, enum.Enum):
    SMALL = 2**6  # 64
    MEDIUM = 2**8  # 256
    LARGE = 2**10  # 1024
    MAXINT4 = 2**31  # Maximum value signed 32-bit integer + 1


class Pattern(str, enum.Enum):
    SENSOR_IDENTIFIER = (  # Version 4 UUID regex
        r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
    )
    SENSOR_NAME = r"^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$"
    VALUE_IDENTIFIER = r"^(?!_)(?!.*__)[a-z_]{1,64}(?<!_)$"
