import json
import typing

import pydantic
import starlette

import app.errors as errors
import app.validation.types as types
from app.logs import logger


# Guidelines for syntactically correct, but otherwise somehow invalid values:
# - When lists of values are passed, ignore any invalid ones
# - When a single value is passed, raise an error


########################################################################################
# Abstract request class
########################################################################################


class _Request(types._BaseModel):
    path: object
    query: object
    body: object


########################################################################################
# Route validation decorator
########################################################################################


def validate(schema: type[_Request]) -> typing.Callable:
    """Decorator to enforce proper validation for the given starlette route."""

    def decorator(func):
        async def wrapper(request: starlette.requests.Request):
            try:
                body = await request.body()
                body = {} if len(body) == 0 else json.loads(body.decode())
                request = schema(
                    path=request.path_params, query=request.query_params, body=body
                )
            except (TypeError, ValueError) as e:
                # TODO Improve log message
                logger.warning(f"[HTTP] Invalid request: {repr(e)}")
                raise errors.BadRequestError()

            return await func(request)

        return wrapper

    return decorator


########################################################################################
# Path models
########################################################################################


class _PostSensorsRequestPath(types._BaseModel):
    pass


class _PutSensorsRequestPath(types._BaseModel):
    sensor_name: types.SensorName


class _StreamSensorsRequestPath(types._BaseModel):
    pass


class _GetMeasurementsRequestPath(types._BaseModel):
    sensor_identifier: types.SensorIdentifier


########################################################################################
# Query models
########################################################################################


class _PostSensorsRequestQuery(types._BaseModel):
    pass


class _PutSensorsRequestQuery(types._BaseModel):
    pass


class _StreamSensorsRequestQuery(types._BaseModel):
    sensor_names: list[types.SensorName]

    # Validators
    _sensor_names_split_string = pydantic.validator(
        "sensor_names", allow_reuse=True, pre=True
    )(types._split_string)


class _GetMeasurementsRequestQuery(types._BaseModel):
    method: typing.Literal[None, "previous", "next"] = None
    creation_timestamp: types.Timestamp = None
    receipt_timestamp: types.Timestamp = None
    position_in_transmission: types.PositiveInteger = None

    @pydantic.validator(
        "creation_timestamp",
        "receipt_timestamp",
        "position_in_transmission",
        always=True,
    )
    def check_exists(cls, v, values, field):
        if values.get("method") is not None and v is None:
            raise ValueError(f"Must specify '{field.name}' when 'method' is specified")
        if values.get("method") is None and v is not None:
            raise ValueError(f"Must specify 'method' when '{field.name}' is specified")
        return v


########################################################################################
# Body models
########################################################################################


class _PostSensorsRequestBody(types._BaseModel):
    sensor_name: types.SensorName
    configuration: types.Json


class _PutSensorsRequestBody(types._BaseModel):
    sensor_name: types.SensorName
    configuration: types.Json


class _StreamSensorsRequestBody(types._BaseModel):
    pass


class _GetMeasurementsRequestBody(types._BaseModel):
    pass


########################################################################################
# Request models
########################################################################################


# TODO Can we generate these automatically?
class PostSensorsRequest(_Request):
    path: _PostSensorsRequestPath
    query: _PostSensorsRequestQuery
    body: _PostSensorsRequestBody


class PutSensorsRequest(_Request):
    path: _PutSensorsRequestPath
    query: _PutSensorsRequestQuery
    body: _PutSensorsRequestBody


class StreamSensorsRequest(_Request):
    path: _StreamSensorsRequestPath
    query: _StreamSensorsRequestQuery
    body: _StreamSensorsRequestBody


class GetMeasurementsRequest(_Request):
    path: _GetMeasurementsRequestPath
    query: _GetMeasurementsRequestQuery
    body: _GetMeasurementsRequestBody
