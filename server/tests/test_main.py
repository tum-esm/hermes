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
async def client():
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    client = httpx.AsyncClient(app=main.app, base_url="http://example.com")
    yield client
    await client.aclose()


def fails(response, error):
    """Check that a httpx request returns with a specific error."""
    if error is None:
        return response.status_code == 200
    return (
        response.status_code == error.STATUS_CODE
        and response.json()["detail"] == error.DETAIL
    )


########################################################################################
# Route: Status
########################################################################################


@pytest.mark.anyio
async def test_reading_server_status(client):
    """Test that correct status data is returned."""
    res = await client.get("/status")
    assert fails(res, None)
    assert set(res.json().keys()) == {
        "environment",
        "commit_sha",
        "branch_name",
        "start_time",
    }
