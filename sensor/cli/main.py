import os
import sys

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

import click
import commands


@click.group()
def cli() -> None:
    pass


cli.add_command(commands.enclosure_arduino, name="enclosure-arduino")
cli.add_command(commands.start, name="start")
cli.add_command(commands.stop, name="stop")
cli.add_command(commands.is_running, name="is-running")


if __name__ == "__main__":
    cli.main(prog_name="insert-name-here-cli")
