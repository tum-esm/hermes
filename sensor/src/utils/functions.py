import os
import random
import signal
import string
import subprocess
import time
from datetime import datetime
from typing import Any, Optional

import gpiozero.pins.pigpio
import pigpio

pigpio.exceptions = False


class CommandLineException(Exception):
    def __init__(self, value: str, details: Optional[str] = None) -> None:
        self.value = value
        self.details = details
        Exception.__init__(self)

    def __str__(self) -> str:
        return repr(self.value)


class ExponentialBackOff:
    def __init__(self) -> None:
        self.backoff_time_bucket_index = 0
        # incremental backoff times on exceptions (1m, 2m, 4m, 8m, 16m, 32m)
        self.backoff_time_buckets = [60, 120, 240, 480, 960, 1920]
        self.next_timer = time.time()

    def reset_timer(self) -> None:
        self.backoff_time_bucket_index = 0

    def next_try_timer(self) -> float:
        """
        Returns the next backoff time
        """
        return self.next_timer

    def set_next_timer(self) -> None:
        """
        Sets next backoff timer
        """
        current_backoff_time = self.backoff_time_buckets[self.backoff_time_bucket_index]

        self.backoff_time_bucket_index = min(
            self.backoff_time_bucket_index + 1,
            len(self.backoff_time_buckets) - 1,
        )

        self.next_timer = time.time() + current_backoff_time


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
    """
    Connects to the active pipiod deamon running on the Pi over network socket.
    Documentation: https://gpiozero.readthedocs.io/en/latest/api_pins.html#gpiozero.pins.pigpio.PiGPIOFactory
    """

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
    while True:
        output: str = "".join(random.choices(string.ascii_lowercase, k=length))
        if output not in forbidden:
            break
    return output


def get_cpu_temperature(simulate: bool = False) -> Optional[float]:
    if simulate:
        return random.uniform(40, 60)
    s = os.popen("vcgencmd measure_temp").readline()
    return float(s.replace("temp=", "").replace("'C\n", ""))


def set_alarm(timeout: int, label: str) -> None:
    """Set an alarm that will raise a `TimeoutError` after `timeout` seconds"""

    def alarm_handler(*_args: Any) -> None:
        raise TimeoutError(f"{label} took too long (timed out after {timeout} seconds)")

    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)


def avg_list(input_list: list[float], round_digits: int = 2) -> float:
    """Averages a list of float.
    Returns a float rounded to defined digits."""
    return round(sum(input_list) / len(input_list), round_digits)


def read_os_uptime() -> int:
    """Reads OS system uptime from terminal and returns time in seconds."""
    uptime_date = subprocess.check_output("uptime -s", shell=True)
    uptime_string = uptime_date.decode("utf-8").strip()
    uptime_datetime = datetime.strptime(uptime_string, "%Y-%m-%d %H:%M:%S")
    uptime_seconds = int(time.time() - uptime_datetime.timestamp())

    return uptime_seconds
