import math
import time
import click
import os
import utils
import src.utils.config_interface


def _start() -> None:
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


def _stop() -> None:
    termination_pids = utils.terminate_processes()
    if len(termination_pids) == 0:
        utils.print_red("No active process to be terminated")
    else:
        utils.print_green(
            f"Terminated {len(termination_pids)} automation background "
            + f"processe(s) with PID(s) {termination_pids}"
        )


@click.command(
    help="Start the automation as a background process. "
    + "Prevents spawning multiple processes"
)
def start() -> None:
    _start()


@click.command(help="Checks whether the background processes are running")
def is_running() -> None:
    existing_pids = utils.get_process_pids()
    if len(existing_pids) > 0:
        utils.print_green(f"background process are running with PID(s) {existing_pids}")
    else:
        utils.print_red("background processes are not running")


@click.command(help="Stop the automation's background process")
def stop() -> None:
    _stop()


@click.command(
    help="Stop and start the automation as a background process. "
    + "Prevents spawning multiple processes and will not perform "
    + "a restart then the calibration might be running"
)
def restart() -> None:
    config = src.utils.config_interface.ConfigInterface.read()
    state = src.utils.StateInterface.read()

    if state.last_calibration_time:
        # calculate configured time until next calibration
        seconds_between_calibrations = (
            3600 * 24 * config.calibration.calibration_frequency_days
        )

        # determine timestamp of next scheduled calibration
        next_calibration = state.last_calibration_time + seconds_between_calibrations

        # summed times per bottle + drying + 15 minutes for safety
        max_calibration_time = (
            config.calibration.sampling_per_cylinder_seconds
            * (len(config.calibration.gas_cylinders) + 1)
            + 900
        )

        if 0 < time.time() - next_calibration < max_calibration_time:
            utils.print_red(
                "Calibration might still be running. Please wait until "
                + "the calibration is finished with the restart"
            )
            return

    utils.print_green("Restarting background process")

    _stop()
    time.sleep(0.5)
    _start()
