import os
import random
import string
import subprocess
from typing import Optional
import pigpio
import gpiozero.pins.pigpio


pigpio.exceptions = False


class CommandLineException(Exception):
    def __init__(self, value: str, details: Optional[str] = None) -> None:
        self.value = value
        self.details = details
        Exception.__init__(self)

    def __str__(self) -> str:
        return repr(self.value)


def run_shell_command(
    command: str,
    working_directory: Optional[str] = None,
) -> str:
    """runs a shell command and raises a CommandLineException if the
    return code is not zero, returns the stdout"""
    p = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_directory,
        env=os.environ.copy(),
        executable="/bin/bash",
    )
    stdout = p.stdout.decode("utf-8", errors="replace").strip()
    stderr = p.stderr.decode("utf-8", errors="replace").strip()
    if p.returncode != 0:
        raise CommandLineException(
            f"command '{command}' failed with exit code {p.returncode}",
            details=f"\nstderr:\n{stderr}\nstout:\n{stdout}",
        )

    return stdout


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


def get_random_string(length: int, forbidden: list[str] = []) -> str:
    """a random string from lowercase letter, the strings from
    the list passed as `forbidden` will not be generated"""
    output: str = ""
    while True:
        output = "".join(random.choices(string.ascii_lowercase, k=length))
        if output not in forbidden:
            break
    return output
