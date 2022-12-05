from typing import Any, Literal
import attrs
import attrs.validators as val


@attrs.frozen
class ConfigSectionGeneral:
    node_id: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(64)]  # type: ignore
    )
    boneless_mode: bool = attrs.field(validator=[val.instance_of(bool)])  # type: ignore


@attrs.frozen
class ConfigSectionMQTT:
    url: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(256)]  # type: ignore
    )
    port: int = attrs.field(validator=[val.instance_of(int), val.ge(0)])  # type: ignore
    identifier: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(3), val.max_len(256)]  # type: ignore
    )
    password: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(8), val.max_len(256)]  # type: ignore
    )
    base_topic: str = attrs.field(
        validator=[val.instance_of(str), val.min_len(1), val.max_len(256)]  # type: ignore
    )


@attrs.frozen
class ConfigSectionValvesAirInlet:
    number: Literal[1, 2, 3, 4] = attrs.field(validator=[val.in_([1, 2, 3, 4])])  # type: ignore
    direction: int = attrs.field(
        validator=[val.instance_of(int), val.ge(0), val.le(359)]  # type: ignore
    )


# necessary because mypyXattr does not support lambda-converters yet
def get_config_section_valves_air_inlets(xs: Any) -> list[ConfigSectionValvesAirInlet]:
    return [ConfigSectionValvesAirInlet(**x) for x in xs]


@attrs.frozen
class ConfigSectionValves:
    air_inlets: list[ConfigSectionValvesAirInlet] = attrs.field(
        validator=[val.instance_of(list)],  # type: ignore
        converter=get_config_section_valves_air_inlets,
    )


# necessary because mypyXattr does not support lambda-converters yet
def get_config_section_general(x: Any) -> ConfigSectionGeneral:
    return ConfigSectionGeneral(**x)


# necessary because mypyXattr does not support lambda-converters yet
def get_config_section_mqtt(x: Any) -> ConfigSectionMQTT:
    return ConfigSectionMQTT(**x)


# necessary because mypyXattr does not support lambda-converters yet
def get_config_section_valves(x: Any) -> ConfigSectionValves:
    return ConfigSectionValves(**x)


@attrs.frozen
class Config:
    """The config.json for each sensor"""

    version: Literal["0.1.0"] = attrs.field(
        validator=[val.instance_of(str), val.in_(["0.1.0"])]
    )
    general: ConfigSectionGeneral = attrs.field(
        converter=get_config_section_general,
    )
    mqtt: ConfigSectionMQTT = attrs.field(
        converter=get_config_section_mqtt,
    )
    valves: ConfigSectionValves = attrs.field(
        converter=get_config_section_valves,
    )


if __name__ == "__main__":
    example_config = {
        "version": "0.1.0",
        "general": {
            "node_id": "a-unique-node-id",
            "boneless_mode": False,
        },
        "mqtt": {
            "url": "...",
            "port": 8883,
            "identifier": "...",
            "password": "........",
            "base_topic": "/.../...",
        },
        "valves": {
            "air_inlets": [
                {"number": 1, "direction": 300},
                {"number": 2, "direction": 50},
            ]
        },
    }
    config = Config(**example_config)  # type: ignore

    print(config)
    # print(config.mqtt.base_topic * 1.7)  # this should throw an error "str * float"
