import attrs


@attrs.frozen
class CO2SensorData:
    raw: float
    compensated: float
    filtered: float


# TODO: add sht 21 data
# TODO: add bm280 data


@attrs.frozen
class WindSensorData:
    direction_min: float
    direction_avg: float
    direction_max: float
    speed_min: float
    speed_avg: float
    speed_max: float
    last_update_time: float


@attrs.frozen
class WindSensorStatus:
    temperature: float
    heating_voltage: float
    supply_voltage: float
    reference_voltage: float
    sensor_id: str
    last_update_time: float
