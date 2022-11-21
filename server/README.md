**Development Setup**

- install the python version noted in `pyproject.toml` via `pyenv`
- install dependencies via `poetry install --with dev --remove-untracked`
- specify your environment variables in a `.env` file (see `.env.example`)
- run tests via `./scripts/test`
- run server in development mode via `./scripts/develop`
