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
    path_parameters: object
    query_parameters: object
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
                    path_parameters=request.path_params,
                    query_parameters=request.query_params,
                    body=body,
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


class _PostSensorsRequestPathParameters(types._BaseModel):
    pass


class _PutSensorsRequestPathParameters(types._BaseModel):
    sensor_name: types.SensorName


class _StreamSensorsRequestPathParameters(types._BaseModel):
    pass


class _GetMeasurementsRequestPathParameters(types._BaseModel):
    sensor_identifier: types.SensorIdentifier


########################################################################################
# Query models
########################################################################################


class _PostSensorsRequestQueryParameters(types._BaseModel):
    pass


class _PutSensorsRequestQueryParameters(types._BaseModel):
    pass


class _StreamSensorsRequestQueryParameters(types._BaseModel):
    sensor_names: list[types.SensorName]

    # Validators
    _sensor_names_split_string = pydantic.validator(
        "sensor_names", allow_reuse=True, pre=True
    )(types._split_string)


class _GetMeasurementsRequestQueryParameters(types._BaseModel):
    method: typing.Literal[None, "previous", "next"] = None
    creation_timestamp: types.Timestamp = None
    receipt_timestamp: types.Timestamp = None
    position_in_transmission: types.PositiveInteger = None


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
    path_parameters: _PostSensorsRequestPathParameters
    query_parameters: _PostSensorsRequestQueryParameters
    body: _PostSensorsRequestBody


class PutSensorsRequest(_Request):
    path_parameters: _PutSensorsRequestPathParameters
    query_parameters: _PutSensorsRequestQueryParameters
    body: _PutSensorsRequestBody


class StreamSensorsRequest(_Request):
    path_parameters: _StreamSensorsRequestPathParameters
    query_parameters: _StreamSensorsRequestQueryParameters
    body: _StreamSensorsRequestBody


class GetMeasurementsRequest(_Request):
    path_parameters: _GetMeasurementsRequestPathParameters
    query_parameters: _GetMeasurementsRequestQueryParameters
    body: _GetMeasurementsRequestBody
