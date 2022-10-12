import asyncio
import databases as dbs
import sqlalchemy

import app.settings as settings


conn = dbs.Database(
    url=settings.POSTGRESQL_URL,
    user=settings.POSTGRESQL_IDENTIFIER,
    password=settings.POSTGRESQL_PASSWORD,
)

measurements = sqlalchemy.Table(
    "measurements",
    sqlalchemy.MetaData(),
    sqlalchemy.Column("timestamp_measurement", sqlalchemy.Integer),
    sqlalchemy.Column("timestamp_receipt", sqlalchemy.Integer),
    sqlalchemy.Column("value", sqlalchemy.Integer),
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
