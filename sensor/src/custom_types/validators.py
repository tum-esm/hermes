import re
from typing import Any, Callable, TypeVar


def validate_bool() -> Callable[[Any, bool], bool]:
    def f(cls: Any, v: Any) -> bool:
        if not isinstance(v, bool):
            raise ValueError(f'"{v}" is not a boolean')
        return v

    return f


def validate_float(
    minimum: float | None = None,
    maximum: float | None = None,
) -> Callable[[Any, float], float]:
    def f(cls: Any, v: float) -> float:
        if not isinstance(v, float):
            raise ValueError(f'"{v}" is not a float')
        if minimum is not None and v < minimum:
            raise ValueError(f'"{v}" is smaller than {minimum}')
        if maximum is not None and v > maximum:
            raise ValueError(f'"{v}" is larger than {maximum}')
        return v

    return f


def validate_int(
    nullable: bool = False,
    minimum: int | None = None,
    maximum: int | None = None,
    allowed: list[int] | None = None,
) -> Callable[[Any, int | None], int | None]:
    def f(cls: Any, v: int | None) -> int | None:
        if v is None:
            if nullable:
                return v
            else:
                raise ValueError(f"value cannot be None")
        if not isinstance(v, int):
            raise ValueError(f'"{v}" is not an integer')
        if minimum is not None and v < minimum:
            raise ValueError(f'"{v}" is smaller than {minimum}')
        if maximum is not None and v > maximum:
            raise ValueError(f'"{v}" is larger than {maximum}')
        if allowed is not None and v not in allowed:
            raise ValueError(f'"{v}" is not a allowed (not one of {allowed})')
        return v

    return f


def validate_str(
    min_len: float | None = None,
    max_len: float | None = None,
    allowed: list[str] | None = None,
    regex: str | None = None,
) -> Callable[[Any, str], str]:
    def f(cls: Any, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f'"{v}" is not a string')
        if min_len is not None and len(v) < min_len:
            raise ValueError(f'"{v}" has less than {min_len} characters')
        if max_len is not None and len(v) > max_len:
            raise ValueError(f'"{v}" has more than {max_len} characters')
        if allowed is not None and v not in allowed:
            raise ValueError(f'"{v}" is not a allowed (not one of {allowed})')
        if regex is not None and re.compile(regex).match(v) is None:
            raise ValueError(f'"{v}" does not match the regex "{regex}"')
        return v

    return f


T = TypeVar("T")


def validate_list(
    min_len: float | None = None,
    max_len: float | None = None,
) -> Callable[[Any, list[T]], list[T]]:
    def f(cls: Any, v: list[T]) -> list[T]:
        if not isinstance(v, list):
            raise ValueError(f'"{v}" is not a list')
        if min_len is not None and len(v) < min_len:
            raise ValueError(f'"{v}" has less than {min_len} elements')
        if max_len is not None and len(v) > max_len:
            raise ValueError(f'"{v}" has more than {max_len} elements')
        return v

    return f
