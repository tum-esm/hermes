import argparse
import asyncio
import os
import json

import asyncpg
import app.database as database


async def _initialize(connection):
    """Initialize the database tables, indexes, and constraints."""
    with open("schema.sql") as file:
        for statement in file.read().split("\n\n\n"):
            await connection.execute(statement)


async def _populate(connection):
    """Populate the database with example data."""
    with open("tests/data.json") as file:
        for table_name, records in json.load(file).items():
            if not records:
                continue
            identifiers = ", ".join([f"${i+1}" for i in range(len(records[0]))])
            await connection.executemany(
                f"INSERT INTO {table_name} VALUES ({identifiers});",
                [tuple(record.values()) for record in records],
            )


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
            await _populate(connection)
    finally:
        await connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--populate", action="store_true")
    args = parser.parse_args()
    asyncio.run(initialize(populate=args.populate))
