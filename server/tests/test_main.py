import asgi_lifespan
import httpx
import pytest

import app.errors as errors
import app.main as main


@pytest.fixture(scope="session")
async def app():
    """Ensure that application startup/shutdown events are called."""
    async with asgi_lifespan.LifespanManager(main.app):
        yield main.app


@pytest.fixture(scope="session")
async def http_client(app):
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as http_client:
        yield http_client


def returns(response, check):
    """Check that a httpx request returns with a specific status code or error."""
    if isinstance(check, int):
        return response.status_code == check
    return response.status_code == check.STATUS_CODE and response.text == check.DETAIL


########################################################################################
# Route: GET /status
########################################################################################


@pytest.mark.anyio
async def test_reading_status(http_client):
    """Test reading the server status."""
    response = await http_client.get("/status")
    assert returns(response, 200)
    assert set(response.json().keys()) == {
        "environment",
        "commit_sha",
        "branch_name",
        "start_time",
    }


########################################################################################
# Route: POST /users
########################################################################################


@pytest.mark.anyio
async def test_creating_user(http_client, cleanup):
    """Test creating a user."""
    response = await http_client.post(
        url="/users",
        json={"username": "squirtle", "password": "12345678"},
    )
    assert returns(response, 201)
    assert set(response.json().keys()) == {"user_identifier", "access_token"}


@pytest.mark.anyio
async def test_creating_user_with_duplicate(http_client, cleanup):
    """Test creating a user when it already exists."""
    response = await http_client.post(
        url="/users",
        json={"username": "squirtle", "password": "12345678"},
    )
    response = await http_client.post(
        url="/users",
        json={"username": "squirtle", "password": "12345678"},
    )
    assert returns(response, errors.ConflictError)


########################################################################################
# Route: POST /sensors
########################################################################################


@pytest.mark.anyio
async def test_creating_sensors(http_client, cleanup):
    """Test creating a sensor."""
    response = await http_client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)


@pytest.mark.anyio
async def test_creating_sensors_with_duplicate(http_client, cleanup):
    """Test creating a sensor that already exists."""
    response = await http_client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)
    response = await http_client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 409)


########################################################################################
# Route: PUT /sensors
########################################################################################


@pytest.mark.anyio
async def test_updating_sensors(http_client, cleanup):
    """Test updating a sensor."""
    response = await http_client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)
    response = await http_client.put(
        url="/sensors/rattata",
        json={"sensor_name": "rattata", "configuration": {"int": 7}},
    )
    assert returns(response, 204)


@pytest.mark.anyio
async def test_updating_sensors_with_not_exists(http_client, cleanup):
    """Test updating a sensor that does not exist."""
    response = await http_client.put(
        url="/sensors/rattata",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 404)


@pytest.mark.anyio
async def test_updating_sensors_with_name_change(http_client, cleanup):
    """Test updating a sensor together with a name change."""
    response = await http_client.post(
        url="/sensors",
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)
    response = await http_client.put(
        url="/sensors/rattata",
        json={"sensor_name": "squirtle", "configuration": {}},
    )
    assert returns(response, 204)
    response = await http_client.put(
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
async def test_reading_sensors(http_client, cleanup):
    """Test reading sensors."""
    response = await http_client.get("/sensors")
    assert returns(response, 200)


@pytest.mark.anyio
async def test_reading_sensors_with_filters(http_client, cleanup):
    """Test reading only specific sensors."""
    response = await http_client.get("/sensors", params={"sensors": "pikachu,squirtle"})
    assert returns(response, 200)


########################################################################################
# Route: GET /measurements
#
# # We don't test a lot here, only a successful response code, because this will change
# a lot in the future.
########################################################################################


@pytest.mark.anyio
async def test_reading_measurements(http_client, cleanup):
    """Test reading measurements."""
    response = await http_client.get("/measurements")
    assert returns(response, 200)


########################################################################################
# Route: POST /authentication
########################################################################################


@pytest.mark.anyio
async def test_creating_session_with_not_exists(http_client, cleanup):
    """Test authenticating a user that doesn't exist."""
    response = await http_client.post(
        url="/authentication",
        json={"username": "magnemite", "password": "12345678"},
    )
    assert returns(response, errors.NotFoundError)
