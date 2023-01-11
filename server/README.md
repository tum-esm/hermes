## Development Setup

- install the python version noted in `pyproject.toml` via `pyenv`
- install dependencies via `poetry install --with dev --remove-untracked`
- run tests via `./scripts/test`
- run server in development mode via `./scripts/develop`

### Deployment

The server is backed by PostgreSQL and an MQTT broker. During development and testing these services are automatically spun up locally for you. In production, it's better to deploy them independently from the server. Cloud providers can help with this.

When you have your PostgreSQL instance and the MQTT broker ready:

- specify your environment variables in a `.env` file (see `.env.example`)
- initialize the database via `(set -a && source .env && ./scripts/initialize)`

The easiest way to deploy the server is via Docker. Many cloud providers offer a way to deploy Docker images automatically from a git repository. If you prefer to build and run the Docker image manually, you can do that via `./scripts/build` and `./scripts/run`.

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
  "configuration": {} // this can be any valid (unnested) JSON object
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
      "severity": "warning", // one of info, warning, error
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
      "value": {} // this can be any valid (unnested) JSON object
    }
  ]
}
```
