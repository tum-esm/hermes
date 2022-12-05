class Constants:
    class Pump:
        control_pin_out = 19
        speed_pin_in = 16
        frequency = 10000

    class Valves:
        pin_1_out = 25
        pin_2_out = 24
        pin_3_out = 23
        pin_4_out = 22

    class UPS:
        ready_pin_in = 5
        battery_mode_pin_in = 10
        alarm_pin_in = 7

    class MainboardSensor:
        i2c_address = 0x76

    class CO2Sensor:
        power_pin_out = 20
        serial_port = "/dev/ttySC0"

    class WindSensor:
        power_pin_out = 21
        serial_port = "/dev/ttySC1"
