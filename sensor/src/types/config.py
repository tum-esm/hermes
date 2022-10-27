from typing import Any, Literal
import attr
import attr.validators as val


@attr.define(frozen=True)
class ConfigSectionGeneral:
    node_id: str = attr.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(64)]  # type: ignore
    )


@attr.define(frozen=True)
class ConfigSectionMQTT:
    base_topic: str = attr.field(
        validator=[val.instance_of(str), val.min_len(1), val.max_len(256)]  # type: ignore
    )
    url: str = attr.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(256)]  # type: ignore
    )
    identifier: str = attr.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(256)]  # type: ignore
    )
    password: str = attr.field(
        validator=[val.instance_of(str), val.min_len(8), val.max_len(256)]  # type: ignore
    )


# necessary because mypyXattr does not support lambda-converters yet
def get_config_section_general(x: Any) -> ConfigSectionGeneral:
    return ConfigSectionGeneral(**x)


# necessary because mypyXattr does not support lambda-converters yet
def get_config_section_mqtt(x: Any) -> ConfigSectionMQTT:
    return ConfigSectionMQTT(**x)


@attr.define(frozen=True)
class Config:
    """The config.json for each sensor"""

    version: Literal["0.1.0"] = attr.field(
        validator=[val.instance_of(str), val.in_(["0.1.0"])]
    )

    general: ConfigSectionGeneral = attr.field(
        converter=get_config_section_general,
    )
    mqtt: ConfigSectionMQTT = attr.field(
        converter=get_config_section_mqtt,
    )


if __name__ == "__main__":
    example_config = {
        "version": "0.1.0",
        "general": {"node_id": "a-unique-node-id"},
        "mqtt": {
            "base_topic": "/.../...",
            "url": "...",
            "identifier": "...",
            "password": "........",
        },
    }
    config = Config(**example_config)  # type: ignore

    print(config)
    # print(config.mqtt.base_topic * 1.7)  # this should throw an error "str * float"
