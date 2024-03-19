The server exposes a REST API. You can find the documentation at [https://bump.sh/empicano/doc/tenta](https://bump.sh/empicano/doc/tenta).

## MQTT communication

The communication between the sensors and the server runs over four MQTT topics:

- `configurations/<sensor-identifier>`: Configurations **to** sensors
- `acknowledgments/<sensor-identifier>`: Configuration acknowledgments **from** sensors
- `measurements/<sensor-identifier>`: Measurements **from** sensors
- `logs/<sensor-identifier>`: Logs **from** sensors

### Payloads

The payloads are JSON encoded and have the following structure:

**`configurations/<sensor-identifier>`:**

```json
{
  "revision": 0,
  "configuration": {} // Can be any valid JSON object
}
```

**`acknowledgments/<sensor-identifier>`:**

```json
// Array structure allows to batch messages
[
  {
    "revision": 0,
    "timestamp": 1683645000.0,
    "success": true // Did the sensor successfully process the configuration?
  }
]
```

**`measurements/<sensor-identifier>`:**

```json
// Array structure allows to batch messages
[
  {
    "revision": 0, // Optional
    "timestamp": 1683645000.0,
    "value": {
      // Data points have type double
      "temperature": 23.1,
      "humidity": 0.62
    }
  }
]
```

**`logs/<sensor-identifier>`:**

```json
// Array structure allows to batch messages
[
  {
    "severity": "error", // One of: info, warning, error
    "revision": 0, // Optional
    "timestamp": 1683645000.0,
    "message": "The CPU is burning; Please call the fire department."
  }
]
```

## Development Setup

- Install the Python version noted in `.python-version` via `pyenv`
- Install the dependencies via `./scripts/setup`
- Run the tests via `./scripts/test`
- Format and lint the code via `./scripts/check`
- Start a development instance with pre-populated example data via `./scripts/develop`

## Deployment

The server is backed by PostgreSQL and an MQTT broker. During development and testing these services are automatically spun up locally for you.

When you have your PostgreSQL instance and the MQTT broker ready:

- specify your environment variables in a `.env` file (see `.env.example`)
- initialize the database via `(set -a && source .env && ./scripts/initialize)`
- build the Docker image via `./scripts/build`


# Docker-based production deployment

This directory contains the necessary files to deploy the hermes server and associated databases using Docker.

# Setup

1. Install Docker and Docker Compose
   ````
   sudo apt install docker docker-compose
   ````
   
2. Install mosquitto
   ````
   sudo apt install mosquitto
   ````
   
3. create a password-file for the mosquitto broker (using username `server`)
   ````
   mosquitto_passwd -c mosquitto_password server
   ````
   
4. Create a `.env` file in this directory with the following content:
   ```` 
   ENVIRONMENT=production
   HERMES_ENVIRONMENT=production
   
   HERMES_POSTGRESQL_PASSWORD=<your-postgresql-password>
   HERMES_POSTGRESQL_URL=127.0.0.1
   HERMES_POSTGRESQL_PORT=5432
   HERMES_POSTGRESQL_IDENTIFIER=postgres
   HERMES_POSTGRESQL_DATABASE=database
   
   HERMES_MQTT_PASSWORD=<your-mosquitto-password>
   HERMES_MQTT_URL=127.0.0.1
   HERMES_MQTT_PORT=1883
   HERMES_MQTT_IDENTIFIER=hermes_server
   HERMES_MQTT_USERNAME=server
   HERMES_MQTT_BASE_TOPIC=sensortopic/
   
   HERMES_MOSQUITTO_PWFILE=./mosquitto_password
   HERMES_MOSQUITTO_DATA_PATH=<path-to-data-dir>/mosquitto
   HERMES_POSTGRESQL_DATA_PATH=<path-to-data-dir>/postgresql
   ````
   
5. Run `docker-compose up` in this directory
   ````
   source .env && docker-compose up
   ````
   
6. If the logs look healthy and everything is working as intended, launch in detached mode
    ````
    source .env && docker-compose up -d
    ````