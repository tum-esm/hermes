#!/bin/bash

export $(grep -v '^#' .env | xargs)

GLOBAL_HERMES_DEPLOYMENT_ROOT_PATH=${HERMES_DEPLOYMENT_ROOT_PATH}
export HERMES_DEPLOYMENT_ROOT_PATH=/root/deployment

# Run the docker image
docker run -it --rm --name hermes_sensor_$HERMES_MQTT_IDENTIFIER \
  --env-file .env \
  -e HERMES_MQTT_IDENTIFIER="$HERMES_MQTT_IDENTIFIER" \
  -e HERMES_DEPLOYMENT_ROOT_PATH="$HERMES_DEPLOYMENT_ROOT_PATH" \
  -v "$GLOBAL_HERMES_DEPLOYMENT_ROOT_PATH":"$HERMES_DEPLOYMENT_ROOT_PATH" \
  tum-esm/hermes/sensor
