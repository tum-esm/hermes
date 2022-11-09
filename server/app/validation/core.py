import abc
import json

import attrs
import starlette

import app.constants as constants
import app.errors as errors
from app.logs import logger


class _RequestQuery:
    pass


class _RequestBody:
    pass


class _Request(abc.ABC):
    """Abstract class for request validation models."""

    @property
    @abc.abstractmethod
    def query(self) -> _RequestQuery:
        pass

    @property
    @abc.abstractmethod
    def body(self) -> _RequestBody:
        pass


async def validate(
    request: starlette.requests.Request,
    schema: type[_Request],
) -> _Request:
    """Validate a starlette request against the given attrs schema."""
    try:
        body = await request.body()
        body = {} if len(body) == 0 else json.loads(body.decode())
        return schema(request.query_params, body)
    except (TypeError, ValueError) as e:
        # TODO Improve log message somehow
        logger.warning(f"[HTTP] InvalidSyntaxError: {e}")
        raise errors.InvalidSyntaxError()
