import click
import sys
import utils
import os

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


@click.command(help="Information about which CLI version and path is used")
def info() -> None:
    click.echo(f"Using Python interpreter at: ", nl=False)
    utils.print_green(sys.executable)
    click.echo(f"Using sensor code at: ", nl=False)
    utils.print_green(PROJECT_DIR)
