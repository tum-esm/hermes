## Development Setup

- install the python version noted in `.python-version` via `pyenv`
- install the dependencies via `poetry install --with dev --sync`
- run the tests via `./scripts/test`
- start a development instance with pre-populated example data via `./scripts/develop`

### Deployment

The server is backed by PostgreSQL and an MQTT broker. During development and testing these services are automatically spun up locally for you. In production, it's better to deploy them independently from the server. Cloud providers can help with this.

When you have your PostgreSQL instance and the MQTT broker ready:

- specify your environment variables in a `.env` file (see `.env.example`)
- initialize the database via `(set -a && source .env && ./scripts/initialize)`
- build the Docker image via `./scripts/build`

## HTTP routes

**`GET /status`:**

Read the status of the server.

```python
httpx.get(url="http://localhost:8000/status")
```

```json
{
  "environment": "production",
  "commit_sha": "1a2984bf5ffda71207fb133d785eb486cb465618",
  "branch_name": "main",
  "start_timestamp": 1674674178.5367813
}
```

**`POST /users`:**

Create a new user.

```python
httpx.post(
    url="http://localhost:8000/users",
    json={"username": "ash", "password": "12345678"},
)
```

```json
{
  "access_token": "c59805ae394cceea937163877ca31375183650586137170a69652b6d8543e869",
  "user_identifier": "575a7328-4e2e-4b88-afcc-e0b5ed3920cc"
}
```

**`POST /authentication`:**

Log in.

```python
httpx.post(
    url="http://localhost:8000/authentication",
    json={"username": "ash", "password": "12345678"},
)
```

```json
{
  "access_token": "c59805ae394cceea937163877ca31375183650586137170a69652b6d8543e869",
  "user_identifier": "575a7328-4e2e-4b88-afcc-e0b5ed3920cc"
}
```

**`GET /networks/<network-identifier>`:**

Read information about the network and its sensors.

```python
httpx.get(
    url="http://localhost:8000/networks/1f705cc5-4242-458b-9201-4217455ea23c",
)
```

```json
[
  {
    "sensor_identifier": "81bf7042-e20f-4a97-ac44-c15853e3618f",
    "sensor_name": "bulbasaur",
    "bucket_timestamps": [],
    "measurements_counts": []
  },
  {
    "sensor_identifier": "2d2a3794-2345-4500-8baa-493f88123087",
    "sensor_name": "charmander",
    "bucket_timestamps": [],
    "measurements_counts": []
  },
  {
    "sensor_identifier": "df1ad8d1-63ea-45b6-ae42-86febb182fe8",
    "sensor_name": "squirtle",
    "bucket_timestamps": [],
    "measurements_counts": []
  }
]
```

**`POST /networks/<network-identifier>/sensors`:**

Create a new sensor.

```python
httpx.post(
    url="http://localhost:8000/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors",
    headers={"authorization": "Bearer c59805ae394cceea937163877ca31375183650586137170a69652b6d8543e869"},
    json={
        "sensor_name": "bulbasaur",
        "configuration": {},
    },
)
```

```json
{
  "sensor_identifier": "81bf7042-e20f-4a97-ac44-c15853e3618f",
  "revision": 0
}
```

**`PUT /networks/<network-identifier>/sensors/<sensor-identifier>`:**

Update the sensor's information and configuration.

```python
httpx.put(
    url="http://localhost:8000/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e",
    headers={"authorization": "Bearer c59805ae394cceea937163877ca31375183650586137170a69652b6d8543e869"},
    json={
        "sensor_name": "bulbasaur",
        "configuration": {
            "value": 23,
            "something": "else",
        },
    },
)
```

```json
{
  "sensor_identifier": "81bf7042-e20f-4a97-ac44-c15853e3618f",
  "revision": 16
}
```

**`GET /networks/<network-identifier>/sensors/<sensor-identifier>/measurements`:**

Read the measurements of a sensor in pages, optionally with keyset query parameters `creation_timestamp` and `direction`.

```python
httpx.get(
    url="http://localhost:8000/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e/measurements",
    params={"direction": "previous"},
)
```

```json
[
  {
    "measurement": {
      "what": 42,
      "tomorrow": true,
      "somewhere": 347
    },
    "revision": 0,
    "creation_timestamp": 1674677601.900101
  },
  {
    "measurement": {
      "what": 42,
      "tomorrow": true,
      "somewhere": 320
    },
    "revision": 2,
    "creation_timestamp": 1674677604.365664
  }
]
```

**`GET /networks/<network-identifier>/sensors/<sensor-identifier>/measurements`:**

Read the logs of a sensor in pages, optionally with keyset query parameters `creation_timestamp` and `direction`.

```python
httpx.get(
    url="http://localhost:8000/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e/logs",
    params={"direction": "previous"},
)
```

```json
[
  {
    "severity": "warning",
    "subject": "The CPU is pretty hot",
    "revision": 0,
    "creation_timestamp": 1674677601.900101,
    "details": null
  },
  {
    "severity": "error",
    "subject": "The CPU is burning",
    "revision": 2,
    "creation_timestamp": 1674677604.365664,
    "details": "Please call the fire department"
  }
]
```

**`GET /networks/<network-identifier>/sensors/<sensor-identifier>/logs/aggregates`:**

Read an aggregate of sensor logs with `warning` and `error` severity.

```python
httpx.get(
    url="http://localhost:8000/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e/logs/aggregates",
)
```

```json
[
  {
    "severity": "warning",
    "subject": "The CPU is pretty hot",
    "min_revision": 0,
    "max_revision": 1,
    "min_creation_timestamp": 1674678353.210926,
    "max_creation_timestamp": 1674678408.210929,
    "count": 3
  },
  {
    "severity": "error",
    "subject": "The CPU is burning",
    "min_revision": 2,
    "max_revision": 2,
    "min_creation_timestamp": 1674678412.210929,
    "max_creation_timestamp": 1674678412.210929,
    "count": 1
  }
]
```

## MQTT

The communication between the sensors and the server runs over four MQTT topics:

- `configurations/<sensor-identifier>` for configurations from the server
- `heartbeats/<sensor-identifier>` for heartbeats and system messages from sensors
- `measurements/<sensor-identifier>` for measurements from sensors
- `log-messages/<sensor-identifier>` for log messages from sensors

### Payloads

The payloads are JSON encoded and have the following structure:

**`configurations/<sensor-identifier>`:**

```json
{
  "revision": 0,
  "configuration": {} // this can be any valid JSON
}
```

**`heartbeats/<sensor-identifier>`:**

```json
{
  // the array structure allows to batch messages
  "heartbeats": [
    {
      "revision": 0,
      "timestamp": 0.0,
      "success": true // did the sensor successfully process the configuration?
    }
  ]
}
```

**`measurements/<sensor-identifier>`:**

```json
{
  // the array structure allows to batch messages
  "measurements": [
    {
      "revision": 0,
      "timestamp": 0.0,
      "value": {} // this can be any valid JSON
    }
  ]
}
```

**`log-messages/<sensor-identifier>`:**

```json
{
  // the array structure allows to batch messages
  "log_messages": [
    {
      "severity": "error", // one of info, warning, error
      "revision": 0,
      "timestamp": 0.0,
      "subject": "The CPU is burning",
      "details": "Please call the fire department" // optional parameter
    }
  ]
}
```
