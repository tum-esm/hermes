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
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    path=request.path_params,
                    query=request.query_params,
                    body=body,
                )
            except (TypeError, ValueError) as e:
                logger.warning(
                    f"[{request.method} {request.url.path}] Request failed validation:"
                    f" {repr(e)}"
                )
                raise errors.BadRequestError()

            return await func(request)

        return wrapper

    return decorator


########################################################################################
# Path models
########################################################################################


class _CreateUserRequestPath(types._BaseModel):
    pass


class _PostSensorsRequestPath(types._BaseModel):
    pass


class _PutSensorsRequestPath(types._BaseModel):
    sensor_name: types.Name


class _GetMeasurementsRequestPath(types._BaseModel):
    sensor_identifier: types.Identifier


class _GetLogMessagesAggregationRequestPath(types._BaseModel):
    sensor_identifier: types.Identifier


class _StreamSensorsRequestPath(types._BaseModel):
    pass


class _CreateSessionRequestPath(types._BaseModel):
    pass


########################################################################################
# Query models
########################################################################################


class _CreateUserRequestQuery(types._BaseModel):
    pass


class _PostSensorsRequestQuery(types._BaseModel):
    pass


class _PutSensorsRequestQuery(types._BaseModel):
    pass


class _GetMeasurementsRequestQuery(types._BaseModel):
    direction: typing.Literal[None, "previous", "next"] = None
    creation_timestamp: types.Timestamp = None

    @pydantic.validator("creation_timestamp", always=True)
    def check_exists(cls, v, values, field):
        if values.get("direction") is not None and v is None:
            raise ValueError(
                f"Must specify '{field.name}' when 'direction' is specified"
            )
        if values.get("direction") is None and v is not None:
            raise ValueError(
                f"Must specify 'direction' when '{field.name}' is specified"
            )
        return v


class _GetLogMessagesAggregationRequestQuery(types._BaseModel):
    pass


class _StreamSensorsRequestQuery(types._BaseModel):
    sensor_names: list[types.Name]

    # Validators
    _sensor_names_split_string = pydantic.validator(
        "sensor_names", allow_reuse=True, pre=True
    )(types._split_string)


class _CreateSessionRequestQuery(types._BaseModel):
    pass


########################################################################################
# Body models
########################################################################################


class _CreateUserRequestBody(types._BaseModel):
    username: types.Name
    password: types.Password


class _PostSensorsRequestBody(types._BaseModel):
    sensor_name: types.Name
    network_identifier: types.Identifier
    configuration: types.Json


class _PutSensorsRequestBody(types._BaseModel):
    sensor_name: types.Name
    configuration: types.Json


class _GetMeasurementsRequestBody(types._BaseModel):
    pass


class _GetLogMessagesAggregationRequestBody(types._BaseModel):
    pass


class _StreamSensorsRequestBody(types._BaseModel):
    pass


class _CreateSessionRequestBody(types._BaseModel):
    username: types.Name
    password: types.Password


########################################################################################
# Request models
# TODO Can we generate these automatically?
########################################################################################


class CreateUserRequest(_Request):
    method: str
    url: object
    headers: dict
    path: _CreateUserRequestPath
    query: _CreateUserRequestQuery
    body: _CreateUserRequestBody


class PostSensorsRequest(_Request):
    method: str
    url: object
    headers: dict
    path: _PostSensorsRequestPath
    query: _PostSensorsRequestQuery
    body: _PostSensorsRequestBody


class PutSensorsRequest(_Request):
    method: str
    url: object
    headers: dict
    path: _PutSensorsRequestPath
    query: _PutSensorsRequestQuery
    body: _PutSensorsRequestBody


class GetMeasurementsRequest(_Request):
    method: str
    url: object
    headers: dict
    path: _GetMeasurementsRequestPath
    query: _GetMeasurementsRequestQuery
    body: _GetMeasurementsRequestBody


class GetLogMessagesAggregationRequest(_Request):
    method: str
    url: object
    headers: dict
    path: _GetLogMessagesAggregationRequestPath
    query: _GetLogMessagesAggregationRequestQuery
    body: _GetLogMessagesAggregationRequestBody


class StreamSensorsRequest(_Request):
    method: str
    url: object
    headers: dict
    path: _StreamSensorsRequestPath
    query: _StreamSensorsRequestQuery
    body: _StreamSensorsRequestBody


class CreateSessionRequest(_Request):
    method: str
    url: object
    headers: dict
    path: _CreateSessionRequestPath
    query: _CreateSessionRequestQuery
    body: _CreateSessionRequestBody
