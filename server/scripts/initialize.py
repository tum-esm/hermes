import argparse
import asyncio
import os
import time

import asyncpg

import app.database as database
import tests.conftest


async def _initialize(connection):
    """Initialize the database tables, indexes, and constraints."""
    with open("schema.sql") as file:
        for statement in file.read().split("\n\n\n"):
            await connection.execute(statement)


async def initialize(populate=False):
    """Initialize the database, optionally populate with example data."""
    try:
        connection = await asyncpg.connect(
            host=os.environ["POSTGRESQL_URL"],
            port=os.environ["POSTGRESQL_PORT"],
            user=os.environ["POSTGRESQL_IDENTIFIER"],
            password=os.environ["POSTGRESQL_PASSWORD"],
            database=os.environ["POSTGRESQL_DATABASE"],
        )
        await database.initialize(connection)
        await _initialize(connection)
        if populate:
            await tests.conftest._populate(
                connection, timestamp=time.time() // 3600 * 3600 - 3600
            )
    finally:
        await connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--populate", action="store_true")
    args = parser.parse_args()
    asyncio.run(initialize(populate=args.populate))
