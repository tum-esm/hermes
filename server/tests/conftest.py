import pytest

import app.main as main


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def cleanup():
    """Delete all data in the database after a test."""
    yield
    async with main.dbpool.acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "user";')
            await connection.execute("DELETE FROM network;")
            await connection.execute("DELETE FROM sensor;")
