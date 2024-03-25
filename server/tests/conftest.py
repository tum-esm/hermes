import contextlib
import json
import os

import asyncpg
import pytest

import app.database as database


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@contextlib.asynccontextmanager
async def _connection():
    """Provide a connection to the database that's properly closed afterwards."""
    try:
        connection = await asyncpg.connect(
            host=os.environ["HERMES_POSTGRESQL_URL"],
            port=os.environ["HERMES_POSTGRESQL_PORT"],
            user=os.environ["HERMES_POSTGRESQL_USERNAME"],
            password=os.environ["HERMES_POSTGRESQL_PASSWORD"],
            database=os.environ["HERMES_POSTGRESQL_DATABASE"],
        )
        await database.initialize(connection)
        yield connection
    finally:
        await connection.close()


@pytest.fixture(scope="session")
async def connection():
    """Provide a database connection is persistent across tests."""
    async with _connection() as connection:
        yield connection


async def _populate(connection):
    """Populate the database with example data."""
    with open("tests/data.json") as file:
        for table_name, records in json.load(file).items():
            identifiers = ", ".join([f"${i+1}" for i in range(len(records[0]))])
            await connection.executemany(
                f'INSERT INTO "{table_name}" VALUES ({identifiers});',
                [tuple(record.values()) for record in records],
            )


@pytest.fixture(scope="function")
async def setup(connection):
    """Reset the database to contain the initial test data for each test."""
    async with connection.transaction():
        # Delete all the data in the database but keep the structure
        await connection.execute('DELETE FROM "user";')
        await connection.execute("DELETE FROM network;")
        await connection.execute("DELETE FROM sensor;")
        # Populate with the initial test data again
        await _populate(connection)
