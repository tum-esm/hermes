import click
import commands


@click.group()
def cli() -> None:
    pass


cli.add_command(commands.start, name="start")
cli.add_command(commands.stop, name="stop")
cli.add_command(commands.is_running, name="is-running")


if __name__ == "__main__":
    cli.main(prog_name="insert-name-here-cli")
