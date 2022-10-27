import time
import click
import os
import utils


@click.command(
    help="Start the automation as a background process. "
    + "Prevents spawning multiple processes"
)
def start() -> None:
    current_pid = utils.process_is_running()
    if current_pid is not None:
        utils.print_red(f"Background process already exists with PID {current_pid}")
    else:
        os.system(f"nohup {utils.INTERPRETER_PATH} {utils.SCRIPT_PATH} &")
        time.sleep(0.5)
        new_pid = utils.process_is_running()
        if new_pid is None:
            utils.print_red(f"Could not start background process")
        else:
            utils.print_green(f"Started background process with PID {new_pid}")
