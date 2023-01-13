import click
from .list_boards import list_boards


@click.group(help="Manage the enclosure arduino board")
def enclosure_arduino() -> None:
    pass


enclosure_arduino.add_command(list_boards, name="list-boards")
