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


def keys(response, keys):
    """Check that a httpx request body contains a specific set of keys."""
    return set(response.json().keys()) == set(keys)


########################################################################################
# Test data
########################################################################################


@pytest.fixture(scope="session")
def identifier():
    return "00000000-0000-4000-8000-000000000000"


@pytest.fixture(scope="session")
def user_identifier():
    return "575a7328-4e2e-4b88-afcc-e0b5ed3920cc"


@pytest.fixture(scope="session")
def network_identifier():
    return "1f705cc5-4242-458b-9201-4217455ea23c"


@pytest.fixture(scope="session")
def sensor_identifier():
    return "81bf7042-e20f-4a97-ac44-c15853e3618f"


@pytest.fixture(scope="session")
def access_token():
    return "c59805ae394cceea937163877ca31375183650586137170a69652b6d8543e869"


########################################################################################
# Route: GET /status
########################################################################################


@pytest.mark.anyio
async def test_read_status(http_client):
    """Test reading the server status."""
    response = await http_client.get("/status")
    assert returns(response, 200)
    assert keys(
        response, {"environment", "commit_sha", "branch_name", "start_timestamp"}
    )


########################################################################################
# Route: POST /users
########################################################################################


@pytest.mark.anyio
async def test_create_user(setup, http_client):
    """Test creating a user."""
    response = await http_client.post(
        url="/users", json={"user_name": "red", "password": "12345678"}
    )
    assert returns(response, 201)
    assert keys(response, {"user_identifier", "access_token"})


@pytest.mark.anyio
async def test_create_user_with_duplicate(setup, http_client):
    """Test creating a user that already exists."""
    response = await http_client.post(
        url="/users", json={"user_name": "ash", "password": "12345678"}
    )
    assert returns(response, errors.ConflictError)


########################################################################################
# Route: POST /authentication
########################################################################################


@pytest.mark.anyio
async def test_create_session(setup, http_client, user_identifier):
    """Test authenticating an existing user with a valid password."""
    response = await http_client.post(
        url="/authentication",
        json={"user_name": "ash", "password": "12345678"},
    )
    assert returns(response, 201)
    assert keys(response, {"user_identifier", "access_token"})
    assert response.json()["user_identifier"] == user_identifier


@pytest.mark.anyio
async def test_create_session_with_invalid_password(setup, http_client):
    """Test authenticating an existing user with an invalid password."""
    response = await http_client.post(
        url="/authentication",
        json={"user_name": "ash", "password": "00000000"},
    )
    assert returns(response, errors.UnauthorizedError)


@pytest.mark.anyio
async def test_create_session_with_not_exists(setup, http_client):
    """Test authenticating a user that doesn't exist."""
    response = await http_client.post(
        url="/authentication",
        json={"user_name": "red", "password": "12345678"},
    )
    assert returns(response, errors.NotFoundError)


########################################################################################
# Route: POST /networks/<network_identifier>/sensors
########################################################################################


@pytest.mark.anyio
async def test_create_sensor(setup, http_client, network_identifier, access_token):
    """Test creating a sensor."""
    response = await http_client.post(
        url=f"/networks/{network_identifier}/sensors",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"sensor_name": "rattata", "configuration": {}},
    )
    assert returns(response, 201)
    assert keys(response, {"sensor_identifier", "revision"})
    assert response.json()["revision"] == 0


@pytest.mark.anyio
async def test_create_sensor_with_duplicate(
    setup, http_client, network_identifier, access_token
):
    """Test creating a sensor that already exists."""
    response = await http_client.post(
        url=f"/networks/{network_identifier}/sensors",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"sensor_name": "bulbasaur", "configuration": {}},
    )
    assert returns(response, errors.ConflictError)


########################################################################################
# Route: PUT /networks/<network_identifier>/sensors/<sensor_identifier>
########################################################################################


@pytest.mark.anyio
async def test_update_sensor(
    setup, http_client, network_identifier, sensor_identifier, access_token
):
    """Test updating a sensor's name and configuration."""
    response = await http_client.put(
        url=f"/networks/{network_identifier}/sensors/{sensor_identifier}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"sensor_name": "rattata", "configuration": {"value": 42}},
    )
    assert returns(response, 200)
    assert keys(response, {"sensor_identifier", "revision"})
    assert response.json()["sensor_identifier"] == sensor_identifier
    assert response.json()["revision"] == 1


@pytest.mark.anyio
async def test_update_sensor_with_not_exists(
    setup, http_client, network_identifier, identifier, access_token
):
    """Test updating a sensor that does not exist."""
    response = await http_client.put(
        url=f"/networks/{network_identifier}/sensors/{identifier}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"sensor_name": "rattata", "configuration": {"value": 42}},
    )
    assert returns(response, errors.NotFoundError)


########################################################################################
# Route: GET /networks/<network_identifier>/sensors/<sensor_identifier>/measurements
########################################################################################


@pytest.mark.anyio
async def test_read_measurements(
    setup, http_client, network_identifier, sensor_identifier
):
    """Test reading the latest measurements."""
    response = await http_client.get(
        url=f"/networks/{network_identifier}/sensors/{sensor_identifier}/measurements",
        params={"direction": "previous"},
    )
    assert returns(response, 200)
    assert isinstance(response.json(), list)
    assert len(response.json()) == 3
    assert [
        set(element.keys()) == {"value", "revision", "creation_timestamp"}
        for element in response.json()
    ]
    assert response.json() == sorted(
        response.json(), key=lambda x: x["creation_timestamp"]
    )


@pytest.mark.anyio
async def test_read_measurements(
    setup, http_client, network_identifier, sensor_identifier
):
    """Test reading measurements before a given timestamp."""
    response = await http_client.get(
        url=f"/networks/{network_identifier}/sensors/{sensor_identifier}/measurements",
        params={"direction": "previous", "creation_timestamp": 180},
    )
    assert returns(response, 200)
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2
    assert [
        set(element.keys()) == {"value", "revision", "creation_timestamp"}
        for element in response.json()
    ]
    assert response.json() == sorted(
        response.json(), key=lambda x: x["creation_timestamp"]
    )


@pytest.mark.anyio
async def test_read_measurements_with_latest(
    setup, http_client, network_identifier, sensor_identifier
):
    """Test reading measurements after a given timestamp."""
    response = await http_client.get(
        url=f"/networks/{network_identifier}/sensors/{sensor_identifier}/measurements",
        params={"direction": "next", "creation_timestamp": 110},
    )
    assert returns(response, 200)
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2
    assert [
        set(element.keys()) == {"value", "revision", "creation_timestamp"}
        for element in response.json()
    ]
    assert response.json() == sorted(
        response.json(), key=lambda x: x["creation_timestamp"]
    )


# TODO check logs
# TODO check log aggregation
# TODO create sensor with missing network
# TODO missing/wrong authentication
