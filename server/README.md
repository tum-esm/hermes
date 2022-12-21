## Development Setup

- install the python version noted in `pyproject.toml` via `pyenv`
- install dependencies via `poetry install --with dev --remove-untracked`
- run tests via `./scripts/test`
- run server in development mode via `./scripts/develop`

### Deployment

- specify your environment variables in a `.env` file (see `.env.example`)
- _more info coming soon_

## MQTT

### Topics

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
  "log-messages": [
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
