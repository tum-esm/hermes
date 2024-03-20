# using base-image containing python3.9, setting shell to use bash by default, switching to /root folder
FROM python:3.9
SHELL ["/bin/bash", "-c"]
WORKDIR /root

# install jq and moreutils (-> sponge)
RUN apt update
RUN apt install -y jq moreutils

# install poetry and set up a venv
RUN python3.9 -m pip install --upgrade pip
RUN python3.9 -m pip install poetry
RUN python3.9 -m venv .venv
RUN source .venv/bin/activate

COPY poetry.lock .
COPY pyproject.toml .
COPY README.md .

# install dependencies through poetry
RUN poetry config installer.max-workers 1
RUN poetry install --with=dev

# copy source directories
COPY cli ./cli
COPY config ./config
COPY data ./data
COPY logs ./logs
COPY scripts ./scripts
COPY src ./src
COPY tests ./tests

COPY run_automation.py .
COPY config/config.template.json ./config/config.json

RUN echo 'HARDWARE_LOCKFILE_PATH="/root/hermes_hardware.lock"' > ./config/.env

ENTRYPOINT ["/root/.venv/bin/python3.9", "/root/run_automation.py"]