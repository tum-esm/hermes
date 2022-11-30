import abc
import json
import typing

import starlette

import app.errors as errors
from app.logs import logger


class _RequestPath:
    pass


class _RequestQuery:
    pass


class _RequestBody:
    pass


class _Request(abc.ABC):
    """Abstract class for request validation models."""

    @property
    @abc.abstractmethod
    def path(self) -> _RequestPath:
        pass

    @property
    @abc.abstractmethod
    def query(self) -> _RequestQuery:
        pass

    @property
    @abc.abstractmethod
    def body(self) -> _RequestBody:
        pass


def validate(schema: type[_Request]) -> typing.Callable:
    """Decorator to enforce proper validation for the given starlette route."""

    def decorator(func):
        async def wrapper(request: starlette.requests.Request):
            try:
                body = await request.body()
                body = {} if len(body) == 0 else json.loads(body.decode())
                request = schema(request.path_params, request.query_params, body)
            except (TypeError, ValueError) as e:
                # TODO Improve log message somehow
                logger.warning(f"[HTTP] Invalid request: {repr(e)}")
                raise errors.BadRequestError()

            return await func(request)

        return wrapper

    return decorator
