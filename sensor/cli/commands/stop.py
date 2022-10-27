import click
import utils


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
