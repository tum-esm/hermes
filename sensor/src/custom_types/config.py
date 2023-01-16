from typing import Literal
from pydantic import BaseModel, validator
from .validators import (
    validate_int,
    validate_str,
    validate_float,
    validate_bool,
    validate_list,
)


class ActiveComponentsConfig(BaseModel):
    measurement: bool
    calibration: bool
    heated_enclosure: bool
    mqtt: bool

    # validators
    _val_bool = validator("*", pre=True, allow_reuse=True)(
        validate_bool(),
    )

    class Config:
        extra = "forbid"


class GeneralConfig(BaseModel):
    station_name: str
    active_components: ActiveComponentsConfig

    # validators
    _val_station_name = validator("station_name", pre=True, allow_reuse=True)(
        validate_str(min_len=3, max_len=64),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class HardwareConfig(BaseModel):
    pumped_litres_per_round: float
    inner_tube_diameter_millimiters: float

    # validators
    _val_pumped_litres_per_round = validator(
        "pumped_litres_per_round", pre=True, allow_reuse=True
    )(
        validate_float(minimum=0.0001, maximum=1),
    )
    _val_inner_tube_diameter_millimiters = validator(
        "inner_tube_diameter_millimiters", pre=True, allow_reuse=True
    )(
        validate_float(minimum=1, maximum=20),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class MeasurementTimingConfig(BaseModel):
    seconds_per_measurement_interval: float
    seconds_per_measurement: float

    # validators
    _val_seconds_per_measurement_interval = validator(
        "seconds_per_measurement_interval", pre=True, allow_reuse=True
    )(
        validate_float(minimum=10, maximum=7200),
    )
    _val_seconds_per_measurement = validator(
        "seconds_per_measurement", pre=True, allow_reuse=True
    )(
        validate_float(minimum=1, maximum=300),
    )

    class Config:
        extra = "forbid"


class MeasurementPumpSpeedConfig(BaseModel):
    litres_per_minute_on_valve_switching: float
    litres_per_minute_on_measurements: float

    # validators
    _val_litres_per_minute_on_valve_switching = validator(
        "litres_per_minute_on_valve_switching", pre=True, allow_reuse=True
    )(
        validate_float(minimum=0.001, maximum=30),
    )
    _val_litres_per_minute_on_measurements = validator(
        "litres_per_minute_on_measurements", pre=True, allow_reuse=True
    )(
        validate_float(minimum=0.001, maximum=30),
    )

    class Config:
        extra = "forbid"


class MeasurementAirInletConfig(BaseModel):
    valve_number: Literal[1, 2, 3, 4]
    direction: int
    tube_length: float

    # validators
    _val_number = validator("valve_number", pre=True, allow_reuse=True)(
        validate_int(allowed=[1, 2, 3, 4]),
    )
    _val_direction = validator("direction", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=359),
    )
    _val_tube_length = validator("tube_length", pre=True, allow_reuse=True)(
        validate_float(minimum=1, maximum=100),
    )

    class Config:
        extra = "forbid"


class MeasurementConfig(BaseModel):
    timing: MeasurementTimingConfig
    pump_speed: MeasurementPumpSpeedConfig
    air_inlets: list[MeasurementAirInletConfig]

    _val_air_inlets = validator("air_inlets", pre=True, allow_reuse=True)(
        validate_list(min_len=1),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class CalibrationGasConfig(BaseModel):
    valve_number: Literal[1, 2, 3, 4]
    concentration: float

    # validators
    _val_valve_number = validator("valve_number", pre=True, allow_reuse=True)(
        validate_int(allowed=[1, 2, 3, 4]),
    )
    _val_concentration = validator("concentration", pre=True, allow_reuse=True)(
        validate_float(minimum=0, maximum=10000),
    )

    class Config:
        extra = "forbid"


class CalibrationConfig(BaseModel):
    flushing_minutes: float
    litres_per_minute: float
    gases: list[CalibrationGasConfig]

    # validators
    _val_flushing_minutes = validator("flushing_minutes", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=60),
    )
    _val_litres_per_minute = validator("litres_per_minute", pre=True, allow_reuse=True)(
        validate_float(minimum=0, maximum=30),
    )

    # we have only implemented multi-point calibration for now
    # that is why min_len=2, but single-point calibration is
    # easy to implement
    _val_gases = validator("gases", pre=True, allow_reuse=True)(
        validate_list(min_len=2),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class HeatedEnclosureConfig(BaseModel):
    device_path: str
    target_temperature: float
    allowed_deviation: float

    # validators
    _val_device_path = validator("device_path", pre=True, allow_reuse=True)(
        validate_str()
    )
    _val_target_temperature = validator(
        "target_temperature", pre=True, allow_reuse=True
    )(
        validate_float(minimum=0, maximum=50),
    )
    _val_allowed_deviation = validator("allowed_deviation", pre=True, allow_reuse=True)(
        validate_float(minimum=0, maximum=10),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class Config(BaseModel):
    """The config.json for each sensor"""

    version: Literal["0.1.0"]
    revision: int
    general: GeneralConfig
    hardware: HardwareConfig
    measurement: MeasurementConfig
    calibration: CalibrationConfig
    heated_enclosure: HeatedEnclosureConfig

    # validators
    _val_version = validator("version", pre=True, allow_reuse=True)(
        validate_str(allowed=["0.1.0"]),
    )
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=2_147_483_648),
    )

    class Config:
        extra = "forbid"
