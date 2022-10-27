import click
from .. import utils


@click.command(help="Checks whether the background process is running")
def is_running() -> None:
    existing_pid = utils.process_is_running()
    if existing_pid is not None:
        utils.print_green(f"background process is running with PID {existing_pid}")
    else:
        utils.print_red("background process is not running")
