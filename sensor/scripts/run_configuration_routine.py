import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

from src import custom_types, utils, procedures

config_request = custom_types.MQTTConfigurationRequest(
    **{
        "revision": 1,
        "configuration": {
            "version": "0.1.0-alpha.3",
            "active_components": {
                "calibration_procedures": False,
                "mqtt_data_sending": True,
                "heated_enclosure_communication": False,
                "pump_speed_monitoring": False,
            },
            "hardware": {
                "pumped_litres_per_round": 0.003,
                "inner_tube_diameter_millimiters": 4,
            },
            "measurement": {
                "timing": {
                    "seconds_per_measurement_interval": 60,
                    "seconds_per_measurement": 10,
                },
                "pumped_litres_per_minute": 4,
                "air_inlets": [
                    {"valve_number": 1, "direction": 300, "tube_length": 50},
                    {"valve_number": 2, "direction": 50, "tube_length": 50},
                ],
            },
            "calibration": {
                "hours_between_calibrations": 25,
                "gases": [
                    {"valve_number": 3, "concentration": 400},
                    {"valve_number": 4, "concentration": 800},
                ],
                "flushing": {"seconds": 300, "pumped_litres_per_minute": 0.5},
                "sampling": {
                    "pumped_litres_per_minute": 0.5,
                    "sample_count": 20,
                    "seconds_per_sample": 300,
                },
                "cleaning": {"seconds": 300, "pumped_litres_per_minute": 0.5},
            },
            "heated_enclosure": {"target_temperature": 25, "allowed_deviation": 3},
        },
    }
)

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    config_procedure = procedures.ConfigurationProcedure(config)
    procedures.MessagingAgent.init(config)

    config_procedure.run(config_request)
