import time
import click
import os
import utils


@click.command(
    help="Start the automation as a background process. "
    + "Prevents spawning multiple processes"
)
def start() -> None:
    current_pids = utils.get_process_pids()
    if len(current_pids) > 0:
        utils.print_red(
            f"Background processes already exists with PID(s) {current_pids}"
        )
    else:
        os.system(f"nohup {utils.INTERPRETER_PATH} {utils.SCRIPT_PATH} &")
        time.sleep(0.5)
        new_pids = utils.get_process_pids()
        if len(new_pids) == 0:
            utils.print_red(f"Could not start background process")
        else:
            utils.print_green(f"Started background process with PID(s) {new_pids}")
