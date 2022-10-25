import pydantic
from typing import Any, Callable


class TypingUtils:
    class ValidationError(Exception):
        """
        Will be raised in any custom checks on TypedDicts
        have failed: file-existence, ip-format, min/max-range
        """

    @staticmethod
    def validate_typed_dict(obj: Any, label: str) -> None:
        class _ValidationModel(pydantic.BaseModel):
            obj: Any

            class Config:
                extra = "forbid"

        try:
            _ValidationModel(obj=obj)
        except pydantic.ValidationError as e:
            pretty_error_messages = []
            for error in e.errors():
                fields = [str(f) for f in error["loc"][1:] if f not in ["__root__"]]
                pretty_error_messages.append(f"{'.'.join(fields)} ({error['msg']})")
            raise TypingUtils.ValidationError(
                f"{label} is invalid: " + ", ".join(pretty_error_messages)
            )

    @staticmethod
    def get_nested_dict_property(obj: Any, property_path: str) -> Any:
        prop = obj
        for key in property_path.split("."):
            prop = prop[key]  # type: ignore
        return prop

    @staticmethod
    def assert_str_len(
        obj: Any, property_path: str, min_len: int, max_len: int
    ) -> None:
        prop: str = TypingUtils.get_nested_dict_property(obj, property_path)
        error_message = (
            f"length of {property_path} must be in range [{min_len}, {max_len}]"
        )
        assert len(prop) >= min_len, error_message
        assert len(prop) <= max_len, error_message

    @staticmethod
    def parse_assertions(assertions: list[Callable[[], None]], label: str) -> None:
        pretty_error_messages = []
        for assertion in assertions:
            try:
                assertion()
            except AssertionError as a:
                pretty_error_messages.append(a.args[0])
            except (TypeError, KeyError):
                # Will be ignored because the structure is already
                # validated. Occurs when property is missing
                pass
        if len(pretty_error_messages) > 0:
            raise TypingUtils.ValidationError(
                f"{label} is invalid: " + ", ".join(pretty_error_messages)
            )
