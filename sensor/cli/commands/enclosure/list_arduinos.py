import click
from src.utils import run_shell_command


@click.command(help="List all connected arduino boards")
def list_arduinos() -> None:
    active_usb_ports = run_shell_command('ls /dev | grep -i "ttyUSB"').split("\n")
    last_arduino_usb_port = run_shell_command(
        'dmesg | grep -i "FTDI USB Serial Device converter now attached to" | tail -n 1'
    ).split(" ")[-1]
    if last_arduino_usb_port in active_usb_ports:
        click.echo(str([last_arduino_usb_port]))
    else:
        click.echo("[]")
