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
    calibration_procedures: bool
    mqtt_communication: bool
    heated_enclosure_communication: bool
    pump_speed_monitoring: bool

    # validators
    _val_bool = validator("*", pre=True, allow_reuse=True)(
        validate_bool(),
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
    seconds_per_measurement_interval: int
    seconds_per_measurement: int

    # validators
    _val_seconds_per_measurement_interval = validator(
        "seconds_per_measurement_interval", pre=True, allow_reuse=True
    )(
        validate_int(minimum=10, maximum=7200),
    )
    _val_seconds_per_measurement = validator(
        "seconds_per_measurement", pre=True, allow_reuse=True
    )(
        validate_int(minimum=1, maximum=300),
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
    pumped_litres_per_minute: float
    air_inlets: list[MeasurementAirInletConfig]

    # validators
    _val_pumped_litres_per_minute = validator(
        "pumped_litres_per_minute", pre=True, allow_reuse=True
    )(
        validate_float(minimum=0.1, maximum=30),
    )
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
    start_timestamp: int
    hours_between_calibrations: float
    seconds_per_gas_bottle: int
    gases: list[CalibrationGasConfig]

    # validators

    _val_start_timestamp = validator("start_timestamp", pre=True, allow_reuse=True)(
        validate_int(minimum=1672531200)  # start 2023-01-01T00:00
    )
    _val_hours_between_calibrations = validator(
        "hours_between_calibrations", pre=True, allow_reuse=True
    )(validate_float(minimum=0.5))
    _val_seconds_per_gas_bottle = validator(
        "seconds_per_gas_bottle", pre=True, allow_reuse=True
    )(validate_int(minimum=6, maximum=1800))
    _val_gases = validator("gases", pre=True, allow_reuse=True)(
        validate_list(min_len=1, max_len=3),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class HeatedEnclosureConfig(BaseModel):
    target_temperature: float
    allowed_deviation: float
    seconds_per_stored_datapoint: int

    # validators
    _val_target_temperature = validator(
        "target_temperature", pre=True, allow_reuse=True
    )(
        validate_float(minimum=0, maximum=50),
    )
    _val_allowed_deviation = validator("allowed_deviation", pre=True, allow_reuse=True)(
        validate_float(minimum=0, maximum=10),
    )
    _val_seconds_per_stored_datapoint = validator(
        "seconds_per_stored_datapoint", pre=True, allow_reuse=True
    )(
        validate_int(minimum=5),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class Config(BaseModel):
    """The config.json for each sensor"""

    version: Literal["0.1.0-beta.2"]
    revision: int
    verbose_logging: bool
    active_components: ActiveComponentsConfig
    hardware: HardwareConfig
    measurement: MeasurementConfig
    calibration: CalibrationConfig
    heated_enclosure: HeatedEnclosureConfig

    # validators
    _val_version = validator("version", pre=True, allow_reuse=True)(
        validate_str(allowed=["0.1.0-beta.2"]),
    )
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=2_147_483_648),
    )
    _val_verbose_logging = validator("verbose_logging", pre=True, allow_reuse=True)(
        validate_bool(),
    )

    class Config:
        extra = "forbid"
