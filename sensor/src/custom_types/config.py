from __future__ import annotations
from typing import Literal, Optional
import pydantic


class ActiveComponentsConfig(pydantic.BaseModel):
    run_calibration_procedures: bool
    send_messages_over_mqtt: bool
    ignore_missing_air_inlet_sensor: bool

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
    calibration_frequency_hours: float = pydantic.Field(..., ge=1)
    sampling_per_cylinder_seconds: int = pydantic.Field(..., ge=6, le=1800)
    start_timestamp: int = pydantic.Field(..., ge=1672531200)  # start 2023-01-01T00:00
    system_flushing_seconds: int = pydantic.Field(..., ge=0, le=600)
    gas_cylinders: list[CalibrationGasConfig] = pydantic.Field(
        ..., min_items=1, max_items=3
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class HardwareConfig(pydantic.BaseModel):
    pump_pwm_duty_cycle: float = pydantic.Field(ge=0, le=1)

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class MeasurementConfig(pydantic.BaseModel):
    average_air_inlet_measurements: int
    procedure_seconds: int = pydantic.Field(..., ge=10, le=7200)
    sensor_frequency_seconds: int = pydantic.Field(..., ge=1, le=300)
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
    hardware: HardwareConfig
    measurement: MeasurementConfig
    verbose_logging: bool

    class Config:
        extra = "forbid"
