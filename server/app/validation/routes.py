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
            body = await request.body()
            try:
                body = {} if len(body) == 0 else json.loads(body.decode())
                request = schema(
                    method=request.method,
                    url=request.url,
                    headers=request.headers,
                    path=request.path_params,
                    query=dict(request.query_params),
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


class _ReadStatusRequestPath(types.LooseModel):
    pass


class _CreateUserRequestPath(types.LooseModel):
    pass


class _CreateSessionRequestPath(types.LooseModel):
    pass


class _CreateSensorRequestPath(types.LooseModel):
    network_identifier: types.Identifier


class _UpdateSensorRequestPath(types.LooseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _CreateConfigurationRequestPath(types.LooseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadConfigurationsRequestPath(types.LooseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadMeasurementsRequestPath(types.LooseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadLogsRequestPath(types.LooseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _ReadLogsAggregatesRequestPath(types.LooseModel):
    network_identifier: types.Identifier
    sensor_identifier: types.Identifier


class _StreamNetworkRequestPath(types.LooseModel):
    network_identifier: types.Identifier
    network_identifier: types.Identifier


########################################################################################
# Query models
########################################################################################


class _ReadStatusRequestQuery(types.LooseModel):
    pass


class _CreateUserRequestQuery(types.LooseModel):
    pass


class _CreateSessionRequestQuery(types.LooseModel):
    pass


class _StreamNetworkRequestQuery(types.LooseModel):
    pass


class _CreateSensorRequestQuery(types.LooseModel):
    pass


class _UpdateSensorRequestQuery(types.LooseModel):
    pass


class _CreateConfigurationRequestQuery(types.LooseModel):
    pass


class _ReadConfigurationsRequestQuery(types.LooseModel):
    revision: types.Revision = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadMeasurementsRequestQuery(types.LooseModel):
    creation_timestamp: types.Timestamp = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadLogsRequestQuery(types.LooseModel):
    creation_timestamp: types.Timestamp = None
    direction: typing.Literal["next", "previous"] = "next"


class _ReadLogsAggregatesRequestQuery(types.LooseModel):
    pass


########################################################################################
# Body models
########################################################################################


class _ReadStatusRequestBody(types.StrictModel):
    pass


class _CreateUserRequestBody(types.StrictModel):
    user_name: types.Name
    password: types.Password


class _CreateSessionRequestBody(types.StrictModel):
    user_name: types.Name
    password: types.Password


class _StreamNetworkRequestBody(types.StrictModel):
    pass


class _CreateSensorRequestBody(types.StrictModel):
    sensor_name: types.Name


class _UpdateSensorRequestBody(types.StrictModel):
    sensor_name: types.Name


class _CreateConfigurationRequestBody(types.Configuration):
    pass


class _ReadConfigurationsRequestBody(types.StrictModel):
    pass


class _ReadMeasurementsRequestBody(types.StrictModel):
    pass


class _ReadLogsRequestBody(types.StrictModel):
    pass


class _ReadLogsAggregatesRequestBody(types.StrictModel):
    pass


########################################################################################
# Request models
# TODO Can we generate these automatically?
########################################################################################


class ReadStatusRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _ReadStatusRequestPath
    query: _ReadStatusRequestQuery
    body: _ReadStatusRequestBody


class CreateUserRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _CreateUserRequestPath
    query: _CreateUserRequestQuery
    body: _CreateUserRequestBody


class CreateSessionRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _CreateSessionRequestPath
    query: _CreateSessionRequestQuery
    body: _CreateSessionRequestBody


class StreamNetworkRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _StreamNetworkRequestPath
    query: _StreamNetworkRequestQuery
    body: _StreamNetworkRequestBody


class CreateSensorRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _CreateSensorRequestPath
    query: _CreateSensorRequestQuery
    body: _CreateSensorRequestBody


class UpdateSensorRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _UpdateSensorRequestPath
    query: _UpdateSensorRequestQuery
    body: _UpdateSensorRequestBody


class CreateConfigurationRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _CreateConfigurationRequestPath
    query: _CreateConfigurationRequestQuery
    body: _CreateConfigurationRequestBody


class ReadConfigurationsRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _ReadConfigurationsRequestPath
    query: _ReadConfigurationsRequestQuery
    body: _ReadConfigurationsRequestBody


class ReadMeasurementsRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _ReadMeasurementsRequestPath
    query: _ReadMeasurementsRequestQuery
    body: _ReadMeasurementsRequestBody


class ReadLogsRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _ReadLogsRequestPath
    query: _ReadLogsRequestQuery
    body: _ReadLogsRequestBody


class ReadLogsAggregatesRequest(types.StrictModel):
    method: str
    url: object
    headers: dict
    path: _ReadLogsAggregatesRequestPath
    query: _ReadLogsAggregatesRequestQuery
    body: _ReadLogsAggregatesRequestBody
