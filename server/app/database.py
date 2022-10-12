import asyncpg as pg
import asyncio

import app.settings as settings


# intialize the connection to the database
conn = asyncio.get_running_loop().run_until_complete(
    pg.connect(
        dsn=settings.POSTGRESQL_URL,
        user=settings.POSTGRESQL_IDENTIFIER,
        password=settings.POSTGRESQL_PASSWORD,
    )
)

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
