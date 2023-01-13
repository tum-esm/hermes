import json
import click
import utils, custom_types
from src.utils import run_shell_command


@click.command(help="List all connected arduino boards")
def list_boards() -> None:
    stdout = run_shell_command("arduino-cli board list --format json")
    try:
        board_list = custom_types.BoardList(boards=json.loads(stdout))
    except Exception as e:
        utils.print_red("command output could not be parsed")
        raise e

    for board in board_list.boards:
        if board.port.protocol_label != "Serial Port (USB)":
            continue
        click.echo(board.port.address)
