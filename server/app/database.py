import json
import typing

import asyncpg
import jinja2
import pendulum

import app.settings as settings


CONFIGURATION = {
    "dsn": settings.POSTGRESQL_URL,
    "user": settings.POSTGRESQL_IDENTIFIER,
    "password": settings.POSTGRESQL_PASSWORD,
}

templates = jinja2.Environment(
    loader=jinja2.PackageLoader(package_name="app", package_path="queries"),
    autoescape=jinja2.select_autoescape(),
)


def dictify(result: typing.Sequence[asyncpg.Record]) -> list[dict]:
    """Cast a database SELECT result into a list of dictionaries."""
    return [dict(record) for record in result]


class Serial(dict):
    def __getitem__(self, key):
        return f"${list(self.keys()).index(key) + 1}"


def build(
    template: str,
    template_parameters: dict[str, typing.Any],
    query_parameters: dict[str, typing.Any],
) -> tuple[str, list[typing.Any]]:
    """Dynamically build asyncpg query.

    1. Render Jinja2 template with the given template parameters
    2. Translate given named query parameters to unnamed asyncpg query parameters

    I don't like how this looks, but I can't find a library that does what I want.
    I think what I'm searching for is a templating library that understands SQL, and
    that outputs SQL strings that can be passed directly to whatever engine I'm using,
    without additional parametrization.

    Using jinja2 seems kind of hacky, because it doesn't help with avoiding SQL
    injections. asyncpg doesn't support named parameters, adding them seems taped on.
    I tried SQLAlchemy, but found it too unflexible and slow to program. I want to
    write directly in SQL and have the queries in separate files.
    """
    query = templates.get_template(template).render(**template_parameters)
    for key in list(query_parameters.keys()):  # copy keys to avoid modifying iterator
        if f"{{{key}}}" not in query:
            query_parameters.pop(key)
    return (
        query.format_map(Serial(**query_parameters)),
        list(query_parameters.values()),
    )


async def initialize(database_client: asyncpg.Connection) -> None:
    """Create tables, and error out if existing tables don't match the schema."""
    tables = ["sensors", "configurations", "measurements"]
    for table in tables:
        await database_client.execute(
            query=templates.get_template(f"create_table_{table}.sql").render()
        )
    # TODO Error out if existing tables don't match the schema


class Client:
    """Custom context manager for asyncpg database connection."""

    def __init__(self, **kwargs):
        self.connection = None
        self.kwargs = kwargs

    async def __aenter__(self):
        self.connection = await asyncpg.connect(**self.kwargs)
        # Automatically encode/decode JSONB fields to/from str
        await self.connection.set_type_codec(
            typename="jsonb",
            schema="pg_catalog",
            encoder=json.dumps,
            decoder=json.loads,
        )
        # Automatically encode/decode TIMSTAMPTZ fields to/from pendulum.DateTime
        await self.connection.set_type_codec(
            typename="timestamptz",
            schema="pg_catalog",
            encoder=lambda x: x.isoformat(),
            decoder=pendulum.parse,
        )
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()
