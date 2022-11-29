import attrs


@attrs.frozen
class CO2SensorData:
    raw: float
    compensated: float
    filtered: float


# TODO: add sht 21 data


@attrs.frozen
class MainboardSensorData:
    """units: °C for temperature, rH for humidity, hPa for pressure"""

    mainboard_temperature: float
    cpu_temperature: float | None
    enclosure_humidity: float
    enclosure_pressure: float


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
