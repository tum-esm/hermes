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


cli.add_command(commands.enclosure, name="enclosure")
cli.add_command(commands.info, name="info")
cli.add_command(commands.is_running, name="is-running")
cli.add_command(commands.start, name="start")
cli.add_command(commands.stop, name="stop")

if __name__ == "__main__":
    cli.main(prog_name="hermes-cli")
