import subprocess
from typing import Optional
import pigpio
import gpiozero.pins.pigpio


pigpio.exceptions = False


def run_shell_command(command: str, working_directory: Optional[str] = None) -> str:
    p = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_directory,
    )
    stdout = p.stdout.decode("utf-8", errors="replace")
    stderr = p.stderr.decode("utf-8", errors="replace")

    assert p.returncode == 0, (
        f"command '{command}' failed with exit code "
        + f"{p.returncode}: stderr = '{stderr}'"
    )
    return stdout.strip()


def get_hostname() -> str:
    raw_hostname = run_shell_command("hostname")
    if "." in raw_hostname:
        return raw_hostname.split(".")[0]
    else:
        return raw_hostname


def distance_between_angles(angle_1: float, angle_2: float) -> float:
    """calculate the directional distance (in degrees) between two angles"""
    if angle_1 > angle_2:
        return min(angle_1 - angle_2, 360 + angle_2 - angle_1)
    else:
        return min(angle_2 - angle_1, 360 + angle_1 - angle_2)


def get_gpio_pin_factory() -> gpiozero.pins.pigpio.PiGPIOFactory:
    """return a PiGPIO pin factory (necessary for hardware PWM for pump)"""
    try:
        pin_factory = gpiozero.pins.pigpio.PiGPIOFactory(host="127.0.0.1")
        assert pin_factory.connection is not None
        assert pin_factory.connection.connected
    except:
        raise ConnectionError(
            'pigpio is not connected, please run "sudo pigpiod -n 127.0.0.1"'
        )
    return pin_factory
