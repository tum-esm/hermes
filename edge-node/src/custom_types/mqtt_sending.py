from typing import Literal, Optional, Union

import pydantic


# -----------------------------------------------------------------------------
# MQTT Config (read from env variables)


class MQTTConfig(pydantic.BaseModel):
    """fixed params loaded from the environment"""

    station_identifier: str = pydantic.Field(..., min_length=3, max_length=256)
    mqtt_url: str = pydantic.Field(..., min_length=3, max_length=256)
    mqtt_port: int = pydantic.Field(..., ge=1, le=65535)
    mqtt_username: str = pydantic.Field(..., min_length=4, max_length=256)
    mqtt_password: str = pydantic.Field(..., min_length=4, max_length=256)
    mqtt_base_topic: str = pydantic.Field(
        ..., max_length=256, regex=r"^([a-z0-9_-]+\/)*$"
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Log Message


class MQTTLogMessageBody(pydantic.BaseModel):
    """message body which is sent to server"""

    severity: Literal["info", "warning", "error"]
    revision: int = pydantic.Field(..., ge=0)
    timestamp: float = pydantic.Field(..., ge=1_640_991_600)
    message: str = pydantic.Field(..., min_length=0)

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Data Message


class MQTTMeasurementData(pydantic.BaseModel):
    gmp343_raw: float
    gmp343_compensated: float
    gmp343_filtered: float
    gmp343_temperature: Optional[float]
    bme280_temperature: Optional[float]
    bme280_humidity: Optional[float]
    bme280_pressure: Optional[float]
    sht45_temperature: Optional[float]
    sht45_humidity: Optional[float]


class MQTTCalibrationData(pydantic.BaseModel):
    cal_bottle_id: float
    cal_gmp343_raw: float
    cal_gmp343_compensated: float
    cal_gmp343_filtered: float
    cal_gmp343_temperature: Optional[float]
    cal_bme280_temperature: Optional[float]
    cal_bme280_humidity: Optional[float]
    cal_bme280_pressure: Optional[float]
    cal_sht45_temperature: Optional[float]
    cal_sht45_humidity: Optional[float]


class MQTTSystemData(pydantic.BaseModel):
    enclosure_bme280_temperature: Optional[float]
    enclosure_bme280_humidity: Optional[float]
    enclosure_bme280_pressure: Optional[float]
    raspi_cpu_temperature: Optional[float]
    raspi_disk_usage: float
    raspi_cpu_usage: float
    raspi_memory_usage: float
    ups_powered_by_grid: float
    ups_battery_is_fully_charged: float
    ups_battery_error_detected: float
    ups_battery_above_voltage_threshold: float


class MQTTWindData(pydantic.BaseModel):
    wxt532_direction_min: float
    wxt532_direction_avg: float
    wxt532_direction_max: float
    wxt532_speed_min: float
    wxt532_speed_avg: float
    wxt532_speed_max: float
    wxt532_last_update_time: float


class MQTTWindSensorInfo(pydantic.BaseModel):
    wxt532_temperature: float
    wxt532_heating_voltage: float
    wxt532_supply_voltage: float
    wxt532_reference_voltage: float
    wxt532_last_update_time: float


class MQTTMeasurementMessageBody(pydantic.BaseModel):
    """message body which is sent to server"""

    revision: int = pydantic.Field(..., ge=0)
    timestamp: float = pydantic.Field(..., ge=1_640_991_600)
    value: Union[
        MQTTMeasurementData,
        MQTTCalibrationData,
        MQTTSystemData,
        MQTTWindData,
        MQTTWindSensorInfo,
    ]

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Acknowledgment Message


class MQTTAcknowledgmentMessageBody(pydantic.BaseModel):
    """message body which is sent to server"""

    revision: int = pydantic.Field(..., ge=0)
    timestamp: float = pydantic.Field(..., ge=1_640_991_600)
    success: bool

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Message Types: Status + Data


class MQTTMessageHeader(pydantic.BaseModel):
    mqtt_topic: Optional[str]
    sending_skipped: bool

    class Config:
        extra = "forbid"


class MQTTLogMessage(pydantic.BaseModel):
    """element in local message queue"""

    header: MQTTMessageHeader
    body: MQTTLogMessageBody

    class Config:
        extra = "forbid"


class MQTTMeasurementMessage(pydantic.BaseModel):
    """element in local message queue"""

    header: MQTTMessageHeader
    body: MQTTMeasurementMessageBody

    class Config:
        extra = "forbid"


class MQTTAcknowledgmentMessage(pydantic.BaseModel):
    """element in local message queue"""

    header: MQTTMessageHeader
    body: MQTTAcknowledgmentMessageBody

    class Config:
        extra = "forbid"


MQTTMessageBody = Union[
    MQTTLogMessageBody, MQTTMeasurementMessageBody, MQTTAcknowledgmentMessageBody
]
MQTTMessage = Union[MQTTLogMessage, MQTTMeasurementMessage, MQTTAcknowledgmentMessage]

# -----------------------------------------------------------------------------
# SQL

# TODO: the record object is typed too strictly, and should allow for arbitrary messages.
#   Type verification is not useful here, as the codebase is not shared with other projects where
#   type checking would make sense to ensure consistency between different projects.
class SQLMQTTRecord(pydantic.BaseModel):
    internal_id: int
    status: Literal["pending", "in-progress"]
    content: MQTTMessage

    class Config:
        extra = "forbid"
