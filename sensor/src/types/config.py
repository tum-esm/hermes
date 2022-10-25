from typing import Literal
import attrs
import attrs.validators as val


@attrs.define(frozen=True)
class ConfigSectionGeneral:
    node_id: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(64)]
    )


@attrs.define(frozen=True)
class ConfigSectionMQTT:
    base_topic: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(1), val.max_len(256)]
    )
    url: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(256)]
    )
    identifier: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(256)]
    )
    password: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(8), val.max_len(256)]
    )


@attrs.define(frozen=True)
class Config:
    """The config.json for each sensor"""

    version: Literal["0.1.0"] = attrs.field(
        validator=[val.instance_of(str), val.in_(["0.1.0"])]
    )
    general: ConfigSectionGeneral = attrs.field(
        converter=lambda x: ConfigSectionGeneral(**x),
    )
    mqtt: ConfigSectionMQTT = attrs.field(
        converter=lambda x: ConfigSectionMQTT(**x),
    )


if __name__ == "__main__":
    config = Config(
        **{
            "version": "0.1.0",
            "general": {"node_id": "a-unique-node-id"},
            "mqtt": {
                "base_topic": "/.../...",
                "url": "...",
                "identifier": "...",
                "password": "........",
            },
        }
    )

    print(config)
    print(config.mqtt.base_topic)
