import asgi_lifespan
import httpx
import pytest

import app.main as main


########################################################################################
# Helper functions
########################################################################################


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def app():
    """Ensure that application startup/shutdown events are called."""
    async with asgi_lifespan.LifespanManager(main.app):
        yield main.app


@pytest.fixture(scope="module")
async def client(app):
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


def returns(response, check):
    """Check that a httpx request returns with a specific status code or error."""
    if isinstance(check, int):
        return response.status_code == check
    return (
        response.status_code == error.STATUS_CODE
        and response.json()["detail"] == error.DETAIL
    )


########################################################################################
# Route: GET /status
########################################################################################


@pytest.mark.anyio
async def test_reading_server_status(client):
    res = await client.get("/status")
    assert returns(res, 200)
    assert set(res.json().keys()) == {
        "environment",
        "commit_sha",
        "branch_name",
        "start_time",
    }


########################################################################################
# Route: POST /sensor
########################################################################################


@pytest.mark.anyio
async def test_creating_sensor(client):
    res = await client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(res, 201)
