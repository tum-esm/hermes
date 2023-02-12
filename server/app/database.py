import json

import asyncpg
import jinja2
import pendulum

import app.settings as settings


templates = jinja2.Environment(
    loader=jinja2.PackageLoader(package_name="app", package_path="queries"),
    autoescape=jinja2.select_autoescape(),
)


def dictify(result):
    """Cast a asyncpg SELECT query result into a list of dictionaries."""
    return [dict(record) for record in result]


def build(template, template_arguments, query_arguments):
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

    TODO remove jinja2 templating
    TODO change named parameters so they're compatible with sqlfluff? (:param?)
    TODO not only remove unused arguments, but fill missing ones with NULL
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


class Client:
    """Custom context manager for asyncpg database connection."""

    def __init__(self):
        self.connection = None

    async def __aenter__(self):
        self.connection = await asyncpg.connect(
            host=settings.POSTGRESQL_URL,
            port=settings.POSTGRESQL_PORT,
            user=settings.POSTGRESQL_IDENTIFIER,
            password=settings.POSTGRESQL_PASSWORD,
            database=settings.POSTGRESQL_DATABASE,
        )
        # Automatically encode/decode TIMESTAMPTZ fields to/from unix timestamps
        await self.connection.set_type_codec(
            typename="timestamptz",
            schema="pg_catalog",
            encoder=lambda x: pendulum.from_timestamp(x).isoformat(),
            decoder=lambda x: pendulum.parse(x).float_timestamp,
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
