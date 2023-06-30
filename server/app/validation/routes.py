import json
import typing

import app.errors as errors
import app.validation.types as types
from app.logs import logger


# Guidelines for syntactically correct, but otherwise somehow invalid values:
# - When lists of values are passed, ignore any invalid ones
# - When a single value is passed, raise an error


########################################################################################
# Route validation decorator
########################################################################################


def validate(schema):
    """Decorator to enforce proper validation for the given starlette route."""

    def decorator(func):
        async def wrapper(request):
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
                    f"{request.method} {request.url.path} -- Request failed validation:"
                    f" {repr(e)}"
                )
                raise errors.BadRequestError()

            return await func(request)

        return wrapper

    return decorator


########################################################################################
# Path models
########################################################################################


class _ReadStatusRequestPath(types._BaseModel):
    pass


class _CreateUserRequestPath(types._BaseModel):
    pass


class _CreateSessionRequestPath(types._BaseModel):
    pass


class _CreateSensorRequestPath(types._BaseModel):
    network_identifier: types.Identifier


class _UpdateSensorRequestPath(types._BaseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _CreateConfigurationRequestPath(types._BaseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadConfigurationsRequestPath(types._BaseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadMeasurementsRequestPath(types._BaseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadLogsRequestPath(types._BaseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadLogsAggregatesRequestPath(types._BaseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _StreamNetworkRequestPath(types._BaseModel):
    network_identifier: types.Identifier
    network_identifier: types.Identifier


########################################################################################
# Query models
########################################################################################


class _ReadStatusRequestQuery(types._BaseModel):
    pass


class _CreateUserRequestQuery(types._BaseModel):
    pass


class _CreateSessionRequestQuery(types._BaseModel):
    pass


class _StreamNetworkRequestQuery(types._BaseModel):
    pass


class _CreateSensorRequestQuery(types._BaseModel):
    pass


class _UpdateSensorRequestQuery(types._BaseModel):
    pass


class _CreateConfigurationRequestQuery(types._BaseModel):
    pass


class _ReadConfigurationsRequestQuery(types._BaseModel):
    revision: types.Revision = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadMeasurementsRequestQuery(types._BaseModel):
    creation_timestamp: types.Timestamp = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadLogsRequestQuery(types._BaseModel):
    creation_timestamp: types.Timestamp = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadLogsAggregatesRequestQuery(types._BaseModel):
    pass


########################################################################################
# Body models
########################################################################################


class _ReadStatusRequestBody(types._BaseModel):
    pass


class _CreateUserRequestBody(types._BaseModel):
    user_name: types.Name
    password: types.Password


class _CreateSessionRequestBody(types._BaseModel):
    user_name: types.Name
    password: types.Password


class _StreamNetworkRequestBody(types._BaseModel):
    pass


class _CreateSensorRequestBody(types._BaseModel):
    sensor_name: types.Name


class _UpdateSensorRequestBody(types._BaseModel):
    sensor_name: types.Name


class _CreateConfigurationRequestBody(types._Configuration):
    pass


class _ReadConfigurationsRequestBody(types._BaseModel):
    pass


class _ReadMeasurementsRequestBody(types._BaseModel):
    pass


class _ReadLogsRequestBody(types._BaseModel):
    pass


class _ReadLogsAggregatesRequestBody(types._BaseModel):
    pass


########################################################################################
# Request models
# TODO Can we generate these automatically?
########################################################################################


class ReadStatusRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _ReadStatusRequestPath
    query: _ReadStatusRequestQuery
    body: _ReadStatusRequestBody


class CreateUserRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _CreateUserRequestPath
    query: _CreateUserRequestQuery
    body: _CreateUserRequestBody


class CreateSessionRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _CreateSessionRequestPath
    query: _CreateSessionRequestQuery
    body: _CreateSessionRequestBody


class StreamNetworkRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _StreamNetworkRequestPath
    query: _StreamNetworkRequestQuery
    body: _StreamNetworkRequestBody


class CreateSensorRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _CreateSensorRequestPath
    query: _CreateSensorRequestQuery
    body: _CreateSensorRequestBody


class UpdateSensorRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _UpdateSensorRequestPath
    query: _UpdateSensorRequestQuery
    body: _UpdateSensorRequestBody


class CreateConfigurationRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _CreateConfigurationRequestPath
    query: _CreateConfigurationRequestQuery
    body: _CreateConfigurationRequestBody


class ReadConfigurationsRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _ReadConfigurationsRequestPath
    query: _ReadConfigurationsRequestQuery
    body: _ReadConfigurationsRequestBody


class ReadMeasurementsRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _ReadMeasurementsRequestPath
    query: _ReadMeasurementsRequestQuery
    body: _ReadMeasurementsRequestBody


class ReadLogsRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _ReadLogsRequestPath
    query: _ReadLogsRequestQuery
    body: _ReadLogsRequestBody


class ReadLogsAggregatesRequest(types._BaseModel):
    method: str
    url: object
    headers: dict
    path: _ReadLogsAggregatesRequestPath
    query: _ReadLogsAggregatesRequestQuery
    body: _ReadLogsAggregatesRequestBody
