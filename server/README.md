## Development Setup

- install the python version noted in `pyproject.toml` via `pyenv`
- install dependencies via `poetry install --with dev --remove-untracked`
- run tests via `./scripts/test`
- run the server in development mode via `./scripts/develop`

### Deployment

The server is backed by PostgreSQL and an MQTT broker. During development and testing these services are automatically spun up locally for you. In production, it's better to deploy them independently from the server. Cloud providers can help with this.

When you have your PostgreSQL instance and the MQTT broker ready:

- specify your environment variables in a `.env` file (see `.env.example`)
- initialize the database via `(set -a && source .env && ./scripts/initialize)`

The easiest way to deploy the server is via Docker. Many cloud providers offer a way to deploy Docker images automatically from a git repository. If you prefer to build and run the Docker image manually, you can do that via `./scripts/build` and `./scripts/run`.

## HTTP routes

**`GET /status`:**

Read the status of the server.

```python
httpx.get(url="http://localhost:8000/status")
```

```javascript
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
    json={"username": "admin", "password": "12345678"},
)
```

```javascript
{
    "access_token": "b6e33a5d4f1dc71b628de55767a6e7bb1087d71fbd60425859251e936bf1ab02",
    "user_identifier": "a8323361-3c22-4f07-8c14-74bb7e8ec3a2"
}
```

**`POST /authentication`:**

Log in.

```python
httpx.post(
    url="http://localhost:8000/authentication",
    json={"username": "admin", "password": "12345678"},
)
```

```javascript
{
    "access_token": "c186a32e88541b4ddb2f0bd59a68b7d68d8f8050757101fa836e2bf9b6bd04c2",
    "user_identifier": "a8323361-3c22-4f07-8c14-74bb7e8ec3a2"
}
```

**`POST /sensors`:**

Create a new sensor.

```python
httpx.post(
    url="http://localhost:8000/sensors",
    headers={"authorization": "Bearer c186a32e88541b4ddb2f0bd59a68b7d68d8f8050757101fa836e2bf9b6bd04c2"},
    json={
        "sensor_name": "bulbasaur",
        "network_identifier": "0a71a8d8-40c6-4086-a64e-58e38350cb53",
        "configuration": {},
    },
)
```

```javascript
{
    "sensor_identifier": "102ebc56-edb9-42be-aec0-15a6c1075c7e",
    "revision": 0
}
```

**`PUT /sensors/<sensor-identifier>`:**

Update the sensor configuration.

```python
httpx.put(
    url="http://localhost:8000/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e",
    headers={"authorization": "Bearer c186a32e88541b4ddb2f0bd59a68b7d68d8f8050757101fa836e2bf9b6bd04c2"},
    json={
        "sensor_name": "bulbasaur",
        "network_identifier": "0a71a8d8-40c6-4086-a64e-58e38350cb53",
        "configuration": {
            "value": 23,
            "something": "else",
        },
    },
)
```

```javascript
{
    "sensor_identifier": "102ebc56-edb9-42be-aec0-15a6c1075c7e",
    "revision": 16
}
```

**`GET /sensors/<sensor-identifier>/measurements`:**

Read the measurements of a sensor in pages, optionally with keyset query parameters `creation_timestamp` and `direction`.

```python
httpx.get(
    url="http://localhost:8000/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e/measurements",
    params={"creation_timestamp": 1674677600.0, "direction": "next"},
)
```

```javascript
[
    {
        "revision": 0,
        "creation_timestamp": 1674677601.900101,
        "measurement": {
            "what": 42,
            "tomorrow": true,
            "somewhere": 347
        }
    },
    {
        "revision": 2,
        "creation_timestamp": 1674677604.365664,
        "measurement": {
            "what": 42,
            "tomorrow": true,
            "somewhere": 320
        }
    }
]
```

**`GET /sensors/<sensor-identifier>/measurements`:**

Read the logs of a sensor in pages, optionally with keyset query parameters `creation_timestamp` and `direction`.

```python
httpx.get(
    url="http://localhost:8000/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e/logs",
    params={"creation_timestamp": 1674677600.0, "direction": "next"},
)
```

```javascript
[
    {
        "revision": 0,
        "creation_timestamp": 1674677601.900101,
        "severity": "warning",
        "subject": "The CPU is pretty hot",
        "details": null
    },
    {
        "revision": 2,
        "creation_timestamp": 1674677604.365664,
        "severity": "error",
        "subject": "The CPU is burning",
        "details": "Please call the fire department"
    }
]
```

**`GET /sensors/<sensor-identifier>/logs/aggregates`:**

Read an aggregate of sensor logs with `warning` and `error` severity.

```python
httpx.get(
    url="http://localhost:8000/sensors/102ebc56-edb9-42be-aec0-15a6c1075c7e/logs/aggregates",
)
```

```javascript
[
    {
        "sensor_identifier": "102ebc56-edb9-42be-aec0-15a6c1075c7e",
        "severity": "warning",
        "subject": "The CPU is pretty hot",
        "min_revision": 0,
        "max_revision": 1,
        "min_creation_timestamp": 1674678353.210926,
        "max_creation_timestamp": 1674678408.210929,
        "count": 3
    },
    {
        "sensor_identifier": "102ebc56-edb9-42be-aec0-15a6c1075c7e",
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

**`GET /streams/<network-identifier>`:**

Stream the activity of sensors via SSE.

```python
httpx.get(
    url="http://localhost:8000/streams/0a71a8d8-40c6-4086-a64e-58e38350cb53",
)
```

## MQTT

The communication between the sensors and the server runs over four MQTT topics:

- `configurations/<sensor-identifier>` for configurations from the server
- `heartbeats/<sensor-identifier>` for heartbeats and system messages from sensors
- `log-messages/<sensor-identifier>` for log messages from sensors
- `measurements/<sensor-identifier>` for measurements from sensors

### Payloads

The payloads are JSON encoded and have the following structure:

**`configurations/<sensor-identifier>`:**

```javascript
{
  "revision": 0,
  "configuration": {} // this can be any valid JSON
}
```

**`heartbeats/<sensor-identifier>`:**

```javascript
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

**`log-messages/<sensor-identifier>`:**

```javascript
{
  // the array structure allows to batch messages
  "log_messages": [
    {
      "severity": "error", // one of debug, info, warning, error
      "revision": 0,
      "timestamp": 0.0,
      "subject": "The CPU is burning",
      "details": "Please call the fire department" // optional parameter
    }
  ]
}
```

**`measurements/<sensor-identifier>`:**

```javascript
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
