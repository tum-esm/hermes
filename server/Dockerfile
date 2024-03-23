FROM python:3.11.0-slim

LABEL maintainer="Felix Böhm <felix@felixboehm.dev>"
LABEL source="https://github.com/tum-esm/insert-name-here"

# Install poetry
ENV POETRY_VERSION=1.4.2 \
    POETRY_HOME=/opt/poetry
RUN python -m venv $POETRY_HOME && \
    $POETRY_HOME/bin/pip install poetry==${POETRY_VERSION}
ENV PATH="${PATH}:${POETRY_HOME}/bin"

# Copy dependency information
COPY pyproject.toml poetry.lock /

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-ansi --no-interaction

EXPOSE 8000

# Read commit hash and branch name as build arguments
ARG commit_sha branch_name
LABEL commit_sha=${commit_sha} branch_name=${branch_name}
ENV HERMES_COMMIT_SHA=${commit_sha} HERMES_BRANCH_NAME=${branch_name}

COPY /app /app

## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.5.0/wait /wait
RUN chmod +x /wait

# generate self-signed SSL certs
COPY docker/gen_cert.sh /gen_cert.sh
RUN chmod +x /gen_cert.sh && /gen_cert.sh tumesm

# set environment variables for SSL-cert and keyfile if not set
RUN if [ -z "$HERMES_SERVER_SSL_KEYFILE" ]; then \
    HERMES_SERVER_SSL_KEYFILE=/self_signed_cert.key; \
fi

RUN if [ -z "$HERMES_SERVER_SSL_CERTFILE" ]; then \
    HERMES_SERVER_SSL_CERTFILE=/self_signed_cert.crt; \
fi

ENV HERMES_SERVER_SSL_KEYFILE=${HERMES_SERVER_SSL_KEYFILE}
ENV HERMES_SERVER_SSL_CERTFILE=${HERMES_SERVER_SSL_CERTFILE}

# wait for dependencies, then launch the server
CMD /wait && poetry run uvicorn app.main:app --ssl-keyfile="$HERMES_SERVER_SSL_KEYFILE" --ssl-certfile="$HERMES_SERVER_SSL_CERTFILE" --host 0.0.0.0 --port 8000 --log-level info
