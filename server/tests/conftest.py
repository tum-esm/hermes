import pytest
import app.main as main


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def cleanup():
    """Delete all data in the database after a test."""
    yield
    await main.database_client.execute("DELETE FROM sensors")
