import asyncio
import databases
import sqlalchemy as sa

import app.settings as settings


def dictify(result):
    """Cast a database SELECT result into a list of dictionaries."""
    return [dict(record) for record in result]


database = databases.Database(
    url=settings.POSTGRESQL_URL,
    user=settings.POSTGRESQL_IDENTIFIER,
    password=settings.POSTGRESQL_PASSWORD,
)

metadata = sa.MetaData()

MEASUREMENTS = sa.Table(
    "measurements",
    metadata,
    sa.Column("node", sa.String(length=32)),
    sa.Column("measurement_timestamp", sa.Integer),
    sa.Column("receipt_timestamp", sa.Integer),
    sa.Column("value", sa.Integer),
)


async def startup():
    await database.connect()


async def shutdown():
    await database.disconnect()
