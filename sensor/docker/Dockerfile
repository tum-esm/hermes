# using base-image containing python3.9, setting shell to use bash by default, switching to /root folder
FROM python:3.10 as build_image
SHELL ["/bin/bash", "-c"]
WORKDIR /root

# install jq and moreutils (-> sponge)
RUN apt update
RUN apt install -y jq moreutils

# install poetry and set up a venv
RUN python3.10 -m pip install --upgrade pip
RUN python3.10 -m pip install poetry
RUN python3.10 -m venv --copies .venv
RUN source .venv/bin/activate

COPY poetry.lock .
COPY pyproject.toml .
COPY README.md .

# install dependencies through poetry
RUN poetry config installer.max-workers 1
RUN poetry install --no-root

COPY config ./config
COPY config/config.template.json ./config/config.json

RUN echo 'HERMES_HARDWARE_LOCKFILE_PATH="/root/hermes_hardware.lock"' >> ./config/.env
RUN echo 'HERMES_DEPLOYMENT_ROOT_PATH="/root/deployment"' >> ./config/.env

FROM python:3.10-slim

RUN apt update
RUN apt install -y wget
RUN python3.10 -m pip install poetry pytest

RUN mkdir -p /root/deployment/0.0.1-alpha.1
WORKDIR /root/deployment/0.0.1-alpha.1
COPY --from=build_image /root/.venv /root/deployment/0.0.1-alpha.1/.venv

# copy source directories
COPY cli ./cli
COPY data ./data
COPY logs ./logs
COPY scripts ./scripts
COPY src ./src
COPY tests ./tests
COPY --from=build_image /root/config ./config

RUN echo "set -o errexit" >> /root/deployment/hermes-cli.sh
RUN echo "/root/deployment/0.0.1-alpha.1/.venv/bin/python3 /root/deployment/0.0.1-alpha.1/cli/main.py \$*" >> /root/deployment/hermes-cli.sh
RUN chmod +x /root/deployment/hermes-cli.sh

COPY run_automation.py .

ENTRYPOINT ["/bin/bash", "/root/deployment/hermes-cli.sh"]