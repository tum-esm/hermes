from __future__ import annotations

from typing import Literal, Optional

import pydantic


class ActiveComponentsConfig(pydantic.BaseModel):
    run_calibration_procedures: bool
    send_messages_over_mqtt: bool
    run_hardware_tests: bool

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class CalibrationGasConfig(pydantic.BaseModel):
    valve_number: Literal[1, 2, 3, 4]
    bottle_id: str

    class Config:
        extra = "forbid"


class CalibrationConfig(pydantic.BaseModel):
    average_air_inlet_measurements: int = pydantic.Field(..., ge=1)
    calibration_frequency_days: int = pydantic.Field(..., ge=1)
    calibration_hour_of_day: int = pydantic.Field(..., ge=0, le=23)
    gas_cylinders: list[CalibrationGasConfig] = pydantic.Field(
        ..., min_items=1, max_items=3
    )
    sampling_per_cylinder_seconds: int = pydantic.Field(..., ge=6, le=1800)
    system_flushing_pump_pwm_duty_cycle: float = pydantic.Field(ge=0, le=1)
    system_flushing_seconds: int = pydantic.Field(..., ge=0, le=600)

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class DocumentationConfig(pydantic.BaseModel):
    site_name: str
    site_short_name: str
    site_observation_since: str
    inlet_elevation: str
    last_maintenance_date: str
    maintenance_comment: str
    gmp343_sensor_id: str

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class HardwareConfig(pydantic.BaseModel):
    pump_pwm_duty_cycle: float = pydantic.Field(ge=0, le=1)
    gmp343_optics_heating: bool
    gmp343_linearisation: bool
    gmp343_temperature_compensation: bool
    gmp343_relative_humidity_compensation: bool
    gmp343_pressure_compensation: bool
    gmp343_oxygen_compensation: bool
    gmp343_filter_seconds_averaging: int = pydantic.Field(..., ge=0, le=60)
    gmp343_filter_smoothing_factor: int = pydantic.Field(..., ge=0, le=255)
    gmp343_filter_median_measurements: int = pydantic.Field(..., ge=0, le=13)

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class MeasurementConfig(pydantic.BaseModel):
    average_air_inlet_measurements: int
    procedure_seconds: int = pydantic.Field(..., ge=10, le=7200)
    valve_number: Literal[1, 2, 3, 4]

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class Config(pydantic.BaseModel):
    """The config.json for each sensor"""

    revision: Optional[int]
    version: str = pydantic.Field(
        regex=r"^\d+\.\d+\.\d+(?:-(?:alpha|beta)\.\d+)?$"
    )  # e.g., "1.2.3" or "99.0.1" or "42.1.0-alpha.6"
    active_components: ActiveComponentsConfig
    calibration: CalibrationConfig
    documentation: DocumentationConfig
    hardware: HardwareConfig
    measurement: MeasurementConfig

    class Config:
        extra = "forbid"
