from pydantic import BaseModel

# validation is only necessary for external sources
# internal source will be covered by mypy


class CO2SensorData(BaseModel):
    raw: float
    compensated: float
    filtered: float


# TODO: add sht 21 data


class MainboardSensorData(BaseModel):
    """units: °C for temperature, rH for humidity, hPa for pressure"""

    mainboard_temperature: float
    cpu_temperature: float | None
    enclosure_humidity: float
    enclosure_pressure: float


class WindSensorData(BaseModel):
    direction_min: float
    direction_avg: float
    direction_max: float
    speed_min: float
    speed_avg: float
    speed_max: float
    last_update_time: float


class WindSensorStatus(BaseModel):
    temperature: float
    heating_voltage: float
    supply_voltage: float
    reference_voltage: float
    sensor_id: str
    last_update_time: float
