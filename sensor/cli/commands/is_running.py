import click
import utils


@click.command(help="Checks whether the background processes are running")
def is_running() -> None:
    existing_pids = utils.get_process_pids()
    if len(existing_pids) > 0:
        utils.print_green(f"background process are running with PID(s) {existing_pids}")
    else:
        utils.print_red("background processes are not running")
