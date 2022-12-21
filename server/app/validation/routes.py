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
    # TODO: Add proper validation for sensor_identifier UUID v4 (see git history)
    sensor_identifier: str


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


# - translate validation completely to pydantic
# - remove hacky jinja2 template stuff
# - finish GET /measurements route
# - change named parameters so they're compatible with sqlfluff? (:param?)


class _GetMeasurementsRequestQueryParameters(types._BaseModel):
    pass


class _GetMeasurementsRequestQueryParameters(types._BaseModel):
    """
    method: str = attrs.field(
        validator=attrs.optional(


    values: list[str] = attrs.field(
        default="",
        converter=_convert_query_string_to_list,
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.instance_of(list),
            member_validator=VALUE_IDENTIFIER_VALIDATOR,
        ),
    )
    start: int = POSITIVE_FLOAT_QUERY_FIELD
    end: int = attrs.field(
        default=None,
        converter=attrs.converters.optional(int),
        validator=attrs.validators.optional(
            attrs.validators.and_(
                POSITIVE_FLOAT_VALIDATOR,
                _validate_end_greater_equal_start,
            )
        ),
    )
    skip: int = attrs.field(
        default=0,
        converter=int,
        validator=POSITIVE_INTEGER_VALIDATOR,
    )
    limit: int = attrs.field(
        default=constants.Limit.MEDIUM,
        converter=int,
        validator=attrs.validators.and_(
            POSITIVE_INTEGER_VALIDATOR,
            attrs.validators.le(constants.Limit.LARGE),
        ),
    )
    """


########################################################################################
# Body models
########################################################################################


class _PostSensorsRequestBody(types._BaseModel):
    sensor_name: types.SensorName
    configuration: dict[types.ValueIdentifier, types.JSONValue]


class _PutSensorsRequestBody(types._BaseModel):
    sensor_name: types.SensorName
    configuration: dict[types.ValueIdentifier, types.JSONValue]


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
