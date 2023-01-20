import click
from .compile_and_upload import compile_and_upload
from .list_arduinos import list_arduinos


@click.group(help="Manage the enclosure arduino board")
def enclosure() -> None:
    pass


enclosure.add_command(list_arduinos, name="list-arduinos")
enclosure.add_command(compile_and_upload, name="compile-and-upload")
