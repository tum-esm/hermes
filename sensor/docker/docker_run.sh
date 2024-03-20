#!/bin/bash

# Run the docker image
docker run -it --rm --name hermes_sensor --env-file .env tum-esm/hermes/sensor
