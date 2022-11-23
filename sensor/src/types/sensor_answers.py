import attrs


@attrs.frozen
class CO2SensorData:
    raw: float
    compensated: float
    filtered: float


# TODO: add sht 21 data
# TODO: add bm280 data
