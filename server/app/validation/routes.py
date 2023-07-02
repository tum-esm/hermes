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


class _ReadStatusRequestPath(types.Model):
    pass


class _CreateUserRequestPath(types.Model):
    pass


class _CreateSessionRequestPath(types.Model):
    pass


class _CreateSensorRequestPath(types.Model):
    network_identifier: types.Identifier


class _UpdateSensorRequestPath(types.Model):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _CreateConfigurationRequestPath(types.Model):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadConfigurationsRequestPath(types.Model):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadMeasurementsRequestPath(types.Model):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadLogsRequestPath(types.Model):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadLogsAggregatesRequestPath(types.Model):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _StreamNetworkRequestPath(types.Model):
    network_identifier: types.Identifier
    network_identifier: types.Identifier


########################################################################################
# Query models
########################################################################################


class _ReadStatusRequestQuery(types.Model):
    pass


class _CreateUserRequestQuery(types.Model):
    pass


class _CreateSessionRequestQuery(types.Model):
    pass


class _StreamNetworkRequestQuery(types.Model):
    pass


class _CreateSensorRequestQuery(types.Model):
    pass


class _UpdateSensorRequestQuery(types.Model):
    pass


class _CreateConfigurationRequestQuery(types.Model):
    pass


class _ReadConfigurationsRequestQuery(types.Model):
    revision: types.Revision = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadMeasurementsRequestQuery(types.Model):
    creation_timestamp: types.Timestamp = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadLogsRequestQuery(types.Model):
    creation_timestamp: types.Timestamp = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadLogsAggregatesRequestQuery(types.Model):
    pass


########################################################################################
# Body models
########################################################################################


class _ReadStatusRequestBody(types.Model):
    pass


class _CreateUserRequestBody(types.Model):
    user_name: types.Name
    password: types.Password


class _CreateSessionRequestBody(types.Model):
    user_name: types.Name
    password: types.Password


class _StreamNetworkRequestBody(types.Model):
    pass


class _CreateSensorRequestBody(types.Model):
    sensor_name: types.Name


class _UpdateSensorRequestBody(types.Model):
    sensor_name: types.Name


class _CreateConfigurationRequestBody(types.Configuration):
    pass


class _ReadConfigurationsRequestBody(types.Model):
    pass


class _ReadMeasurementsRequestBody(types.Model):
    pass


class _ReadLogsRequestBody(types.Model):
    pass


class _ReadLogsAggregatesRequestBody(types.Model):
    pass


########################################################################################
# Request models
# TODO Can we generate these automatically?
########################################################################################


class ReadStatusRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _ReadStatusRequestPath
    query: _ReadStatusRequestQuery
    body: _ReadStatusRequestBody


class CreateUserRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _CreateUserRequestPath
    query: _CreateUserRequestQuery
    body: _CreateUserRequestBody


class CreateSessionRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _CreateSessionRequestPath
    query: _CreateSessionRequestQuery
    body: _CreateSessionRequestBody


class StreamNetworkRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _StreamNetworkRequestPath
    query: _StreamNetworkRequestQuery
    body: _StreamNetworkRequestBody


class CreateSensorRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _CreateSensorRequestPath
    query: _CreateSensorRequestQuery
    body: _CreateSensorRequestBody


class UpdateSensorRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _UpdateSensorRequestPath
    query: _UpdateSensorRequestQuery
    body: _UpdateSensorRequestBody


class CreateConfigurationRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _CreateConfigurationRequestPath
    query: _CreateConfigurationRequestQuery
    body: _CreateConfigurationRequestBody


class ReadConfigurationsRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _ReadConfigurationsRequestPath
    query: _ReadConfigurationsRequestQuery
    body: _ReadConfigurationsRequestBody


class ReadMeasurementsRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _ReadMeasurementsRequestPath
    query: _ReadMeasurementsRequestQuery
    body: _ReadMeasurementsRequestBody


class ReadLogsRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _ReadLogsRequestPath
    query: _ReadLogsRequestQuery
    body: _ReadLogsRequestBody


class ReadLogsAggregatesRequest(types.Model):
    method: str
    url: object
    headers: dict
    path: _ReadLogsAggregatesRequestPath
    query: _ReadLogsAggregatesRequestQuery
    body: _ReadLogsAggregatesRequestBody
