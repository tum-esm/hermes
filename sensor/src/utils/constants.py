class Constants:
    class pump:
        control_pin_out = 19
        speed_pin_in = 16
        frequency = 10000

    class valves:
        pin_1_out = 25
        pin_2_out = 24
        pin_3_out = 23
        pin_4_out = 22

    class ups:
        ready_pin_in = 5
        battery_mode_pin_in = 10
        alarm_pin_in = 7

    class mainboard_sensor:
        i2c_address = 0x76

    class co2_sensor:
        power_pin_out = 20
