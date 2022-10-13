import asyncio
import databases
import sqlalchemy as sqla

import app.settings as settings


conn = databases.Database(
    url=settings.POSTGRESQL_URL,
    user=settings.POSTGRESQL_IDENTIFIER,
    password=settings.POSTGRESQL_PASSWORD,
)

measurements = sqla.Table(
    "measurements",
    sqla.MetaData(),
    sqla.Column("timestamp_measurement", sqla.Integer),
    sqla.Column("timestamp_receipt", sqla.Integer),
    sqla.Column("value", sqla.Integer),
)


async def startup():
    await conn.connect()


async def shutdown():
    await conn.disconnect()


'''
# set up the measurements table
asyncio.get_running_loop().run_until_complete(
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS measurements (
            timestamp_measurement   integer,
            timestamp_receipt       integer,
            value                   integer
        );
    """
    )
)
'''
