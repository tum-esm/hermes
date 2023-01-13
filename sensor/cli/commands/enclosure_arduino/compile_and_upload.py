import click
from src.utils import ConfigInterface
from src.hardware_interfaces import HeatedEnclosureInterface


@click.command(help="Compile and upload the code to the arduino")
def compile_and_upload() -> None:
    config = ConfigInterface.read()

    click.echo("compiling")
    HeatedEnclosureInterface.compile_firmware(config)

    click.echo("uploading")
    HeatedEnclosureInterface.upload_firmware(config)

    click.echo("done")
