import click
from src.hardware import HeatedEnclosureInterface


@click.command(help="Get the arduino's USB port (the arduino connected last)")
def list_arduinos() -> None:
    try:
        click.echo(HeatedEnclosureInterface.get_arduino_address())
    except HeatedEnclosureInterface.DeviceFailure:
        click.echo("no Arduino found")
        exit(-1)
