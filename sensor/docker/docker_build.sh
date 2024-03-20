#!/bin/bash

# Build the docker image
docker build -t tum-esm/hermes/sensor -f $(dirname "$0")/Dockerfile $(dirname "$0")/../