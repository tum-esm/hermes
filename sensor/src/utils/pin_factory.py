from gpiozero.pins.pigpio import PiGPIOFactory


def get_pin_factory() -> PiGPIOFactory:
    """return a PiGPIO pin factory (necessary for hardware PWM for pump)"""
    pin_factory = PiGPIOFactory(host="127.0.0.1")
    pi_error_message = 'pigpio is not connected, please run "sudo pigpiod -n 127.0.0.1"'
    assert pin_factory.connection is not None, pi_error_message
    assert pin_factory.connection.connected, pi_error_message
    return pin_factory
