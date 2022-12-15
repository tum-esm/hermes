import pigpio
from gpiozero.pins.pigpio import PiGPIOFactory


pigpio.exceptions = False


def get_pin_factory() -> PiGPIOFactory:
    """return a PiGPIO pin factory (necessary for hardware PWM for pump)"""
    try:
        pin_factory = PiGPIOFactory(host="127.0.0.1")
        assert pin_factory.connection is not None
        assert pin_factory.connection.connected
    except:
        raise ConnectionError(
            'pigpio is not connected, please run "sudo pigpiod -n 127.0.0.1"'
        )
    return pin_factory
