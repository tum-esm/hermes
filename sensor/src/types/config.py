from typing import Literal
import attrs


@attrs.define(frozen=True)
class ConfigSectionGeneral:
    node_id: str = attrs.field(
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.min_len(3),
            attrs.validators.max_len(128),
        ]
    )


@attrs.define(frozen=True)
class Config:
    """The config.json for each sensor"""

    version: Literal["0.1.0"] = attrs.field(
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(["0.1.0"]),
        ]
    )
    general: ConfigSectionGeneral = attrs.field(
        converter=lambda x: ConfigSectionGeneral(**x)
    )


if __name__ == "__main__":
    a = Config(**{"version": "0.1.0", "general": {"node_id": "a"}})

    print(a.general.node_id)
