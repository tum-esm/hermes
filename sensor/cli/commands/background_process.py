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


@click.command(help="Checks whether the background processes are running")
def is_running() -> None:
    existing_pids = utils.get_process_pids()
    if len(existing_pids) > 0:
        utils.print_green(f"background process are running with PID(s) {existing_pids}")
    else:
        utils.print_red("background processes are not running")


@click.command(help="Stop the automation's background process")
def stop() -> None:
    termination_pids = utils.terminate_processes()
    if len(termination_pids) == 0:
        utils.print_red("No active process to be terminated")
    else:
        utils.print_green(
            f"Terminated {len(termination_pids)} automation background "
            + f"processe(s) with PID(s) {termination_pids}"
        )
