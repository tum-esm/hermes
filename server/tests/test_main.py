import asgi_lifespan
import httpx
import pytest

import app.main as main


@pytest.fixture(scope="session")
async def app():
    """Ensure that application startup/shutdown events are called."""
    async with asgi_lifespan.LifespanManager(main.app):
        yield main.app


@pytest.fixture(scope="session")
async def client(app):
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


def returns(response, check):
    """Check that a httpx request returns with a specific status code or error."""
    if isinstance(check, int):
        return response.status_code == check
    return (
        response.status_code == check.STATUS_CODE
        and response.json()["detail"] == check.DETAIL
    )


########################################################################################
# Route: GET /status
########################################################################################


@pytest.mark.anyio
async def test_reading_status(client):
    """Test reading the server status."""
    response = await client.get("/status")
    assert returns(response, 200)
    assert set(response.json().keys()) == {
        "environment",
        "commit_sha",
        "branch_name",
        "start_time",
    }


########################################################################################
# Route: POST /sensors
########################################################################################


@pytest.mark.anyio
async def test_creating_sensors(client, cleanup):
    """Test creating a sensor."""
    response = await client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)


@pytest.mark.anyio
async def test_creating_sensors_with_duplicate(client, cleanup):
    """Test creating a sensor that already exists."""
    response = await client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)
    response = await client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 409)


########################################################################################
# Route: PUT /sensors
########################################################################################


@pytest.mark.anyio
async def test_updating_sensors(client, cleanup):
    """Test updating a sensor."""
    response = await client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)
    response = await client.put(
        url="/sensors/rattata",
        json={"sensor_name": "rattata", "configuration": {"int": 7}},
    )
    assert returns(response, 204)


@pytest.mark.anyio
async def test_updating_sensors_with_not_exists(client, cleanup):
    """Test updating a sensor that does not exist."""
    response = await client.put(
        url="/sensors/rattata",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 404)


@pytest.mark.anyio
async def test_updating_sensors_with_name_change(client, cleanup):
    """Test updating a sensor together with a name change."""
    response = await client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)
    response = await client.put(
        url="/sensors/rattata",
        json={"sensor_name": "squirtle", "configuration": {}},
    )
    assert returns(response, 204)
    response = await client.put(
        url="/sensors/squirtle",
        json={"sensor_name": "squirtle", "configuration": {}},
    )
    assert returns(response, 204)


########################################################################################
# Route: GET /sensors
#
# We don't test a lot here, only a successful response code, because this will change
# a lot in the future.
#
# TODO add default data that is reset before every test
########################################################################################


@pytest.mark.anyio
async def test_reading_sensors(client, cleanup):
    """Test reading sensors."""
    response = await client.get("/sensors")
    assert returns(response, 200)


@pytest.mark.anyio
async def test_reading_sensors_with_filter(client, cleanup):
    """Test reading only specific sensors."""
    response = await client.get("/sensors", params={"sensors": "pikachu,squirtle"})
    assert returns(response, 200)


########################################################################################
# Route: GET /measurements
#
# # We don't test a lot here, only a successful response code, because this will change
# a lot in the future.
########################################################################################


@pytest.mark.anyio
async def test_reading_measurements(client, cleanup):
    """Test reading measurements."""
    response = await client.get("/measurements")
    assert returns(response, 200)
