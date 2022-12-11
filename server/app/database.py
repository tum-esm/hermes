import json
import typing

import asyncpg
import jinja2

import app.settings as settings


templates = jinja2.Environment(
    loader=jinja2.PackageLoader(package_name="app", package_path="queries"),
    autoescape=jinja2.select_autoescape(),
)


def dictify(result: typing.Sequence[asyncpg.Record]) -> list[dict]:
    """Cast a database SELECT result into a list of dictionaries."""
    return [dict(record) for record in result]


def build(
    template: str,
    template_arguments: dict[str, typing.Any],
    query_arguments: dict[str, typing.Any] | list[dict[str, typing.Any]],
) -> tuple[str, tuple[typing.Any, ...] | list[tuple[typing.Any, ...]]]:
    """Dynamically build and parametrize asyncpg query.

    1. Render Jinja2 template with the given template arguments
    2. Translate given named query arguments to unnamed asyncpg query arguments

    I don't like how this looks, but I can't find a library that does what I want.
    I think what I'm searching for is a templating library that understands SQL, and
    that outputs SQL strings that can be passed directly to whatever engine I'm using,
    without additional parametrization.

    Using jinja2 seems kind of hacky, because it doesn't help with avoiding SQL
    injections. asyncpg doesn't support named arguments, adding them seems taped on.
    I tried SQLAlchemy, but found it too unflexible and slow to program. I want to
    write directly in SQL and have the queries in separate files.
    """
    query = templates.get_template(template).render(**template_arguments)
    # Get the names of the query arguments in some fixed order
    keys = list(
        query_arguments.keys()
        if isinstance(query_arguments, dict)
        else query_arguments[0].keys()
    )
    # Remove keys that are not used in the query template
    keys = [key for key in keys if f"{{{key}}}" in query]
    # Replace named arguments with native numbered arguments
    query = query.format_map({key: f"${index + 1}" for index, key in enumerate(keys)})
    # Build the tuple (or list of tuples) of arguments
    arguments = (
        tuple(query_arguments[key] for key in keys)
        if isinstance(query_arguments, dict)
        else [tuple(x[key] for key in keys) for x in query_arguments]
    )
    return query, arguments  # type: ignore


async def setup(database_client: asyncpg.Connection) -> None:
    """Create tables, and error out if existing tables don't match the schema."""
    await database_client.execute(templates.get_template("initialize.sql").render())
    tables = ["sensors", "configurations", "measurements"]
    for table in tables:
        await database_client.execute(
            templates.get_template(f"create-table-{table}.sql").render()
        )
    # TODO Error out if existing tables don't match the schema


class Client:
    """Custom context manager for asyncpg database connection."""

    def __init__(self):
        self.connection = None

    async def __aenter__(self):
        self.connection = await asyncpg.connect(
            host=settings.POSTGRESQL_URL,
            user=settings.POSTGRESQL_IDENTIFIER,
            password=settings.POSTGRESQL_PASSWORD,
            database=settings.POSTGRESQL_DATABASE,
        )
        # Automatically encode/decode JSONB fields to/from str
        await self.connection.set_type_codec(
            typename="jsonb",
            schema="pg_catalog",
            encoder=json.dumps,
            decoder=json.loads,
        )
        # Automatically encode/decode UUID fields to/from str
        await self.connection.set_type_codec(
            typename="uuid",
            schema="pg_catalog",
            encoder=str,
            decoder=str,
        )
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()
