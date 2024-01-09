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


class HardwareConfig(pydantic.BaseModel):
    pump_pwm_duty_cycle: float = pydantic.Field(ge=0, le=1)

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class MeasurementTimingConfig(pydantic.BaseModel):
    measurement_procedure_seconds: int = pydantic.Field(..., ge=10, le=7200)
    measurement_frequency_seconds: int = pydantic.Field(..., ge=1, le=300)

    class Config:
        extra = "forbid"


class MeasurementAirInletConfig(pydantic.BaseModel):
    valve_number: Literal[1, 2, 3, 4]
    direction: int = pydantic.Field(..., ge=0, le=359)
    tube_length: float = pydantic.Field(..., ge=1, le=100)

    class Config:
        extra = "forbid"


class MeasurementConfig(pydantic.BaseModel):
    timing: MeasurementTimingConfig
    air_inlets: list[MeasurementAirInletConfig] = pydantic.Field(
        min_items=1, max_items=4
    )
    average_air_inlet_measurements: int

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class CalibrationTimingConfig(pydantic.BaseModel):
    start_timestamp: int = pydantic.Field(..., ge=1672531200)  # start 2023-01-01T00:00
    hours_between_calibrations: float = pydantic.Field(..., ge=1)
    seconds_per_gas_bottle: int = pydantic.Field(..., ge=6, le=1800)
    system_flushing_seconds: int = pydantic.Field(..., ge=0, le=600)

    class Config:
        extra = "forbid"


class CalibrationGasConfig(pydantic.BaseModel):
    valve_number: Literal[1, 2, 3, 4]
    bottle_id: str

    class Config:
        extra = "forbid"


class CalibrationConfig(pydantic.BaseModel):
    timing: CalibrationTimingConfig
    gases: list[CalibrationGasConfig] = pydantic.Field(..., min_items=1, max_items=3)
    average_air_inlet_measurements: int

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------


class Config(pydantic.BaseModel):
    """The config.json for each sensor"""

    revision: Optional[int]
    version: str = pydantic.Field(
        regex=r"^\d+\.\d+\.\d+(?:-(?:alpha|beta)\.\d+)?$"
    )  # e.g., "1.2.3" or "99.0.1" or "42.1.0-alpha.6"
    verbose_logging: bool
    active_components: ActiveComponentsConfig
    hardware: HardwareConfig
    measurement: MeasurementConfig
    calibration: CalibrationConfig

    class Config:
        extra = "forbid"
