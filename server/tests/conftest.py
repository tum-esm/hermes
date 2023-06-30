import json

import pytest

import app.main as main


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


async def _reset(connection):
    """Delete all the data in the database but keep the structure."""
    await connection.execute('DELETE FROM "user";')
    await connection.execute("DELETE FROM network;")
    await connection.execute("DELETE FROM sensor;")


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
async def setup():
    """Reset the database to contain the initial test data for each test."""
    async with main.dbpool.acquire() as connection:
        async with connection.transaction():
            await _reset(connection)
            await _populate(connection)
