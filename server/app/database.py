import contextlib
import json

import asyncpg
import pendulum

import app.settings as settings


def prepare():
    with open("app/queries.sql", "r") as file:
        statements = file.read().split("\n\n\n")
        # Validate format
        assert all(statement.startswith("-- name: ") for statement in statements)
        assert not any("\n-- name: " in statement for statement in statements)
        return {
            statement.split("\n", 1)[0][9:]: statement.split("\n", 1)[1]
            for statement in statements
        }


queries = prepare()


def parametrize(query, arguments):
    """Parametrize query and translate named parameters into valid PostgreSQL.

    TODO not only remove unused arguments, but fill missing ones with NULL
    """
    query = queries[query]
    # Get the names of the query arguments in some fixed order
    keys = list(
        arguments.keys() if isinstance(arguments, dict) else arguments[0].keys()
    )
    # Remove keys that are not used in the query template
    keys = [key for key in keys if f"${{{key}}}" in query]
    # Replace named arguments with native numbered arguments
    query = query.format_map({key: str(index + 1) for index, key in enumerate(keys)})
    # Build the tuple (or list of tuples) of arguments
    arguments = (
        tuple(arguments[key] for key in keys)
        if isinstance(arguments, dict)
        else [tuple(x[key] for key in keys) for x in arguments]
    )
    return query, arguments


def dictify(result):
    """Cast a asyncpg SELECT query result into a list of dictionaries."""
    # TODO: implement this as a custom asyncpg record_class on pool?
    # see https://magicstack.github.io/asyncpg/current/api/index.html#connection-pools
    return [dict(record) for record in result]


async def initialize(connection):
    # Automatically encode/decode TIMESTAMPTZ fields to/from unix timestamps
    await connection.set_type_codec(
        typename="timestamptz",
        schema="pg_catalog",
        encoder=lambda x: pendulum.from_timestamp(x).isoformat(),
        decoder=lambda x: pendulum.parse(x).float_timestamp,
    )
    # Automatically encode/decode JSONB fields to/from str
    await connection.set_type_codec(
        typename="jsonb",
        schema="pg_catalog",
        encoder=json.dumps,
        decoder=json.loads,
    )
    # Automatically encode/decode UUID fields to/from str
    await connection.set_type_codec(
        typename="uuid",
        schema="pg_catalog",
        encoder=str,
        decoder=str,
    )


@contextlib.asynccontextmanager
async def pool():
    """Context manager for asyncpg database pool with custom settings."""
    async with asyncpg.create_pool(
        host=settings.POSTGRESQL_URL,
        port=settings.POSTGRESQL_PORT,
        user=settings.POSTGRESQL_IDENTIFIER,
        password=settings.POSTGRESQL_PASSWORD,
        database=settings.POSTGRESQL_DATABASE,
        min_size=2,
        max_size=4,
        max_queries=16384,
        max_inactive_connection_lifetime=300,
        init=initialize,
    ) as x:
        yield x
