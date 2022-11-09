set -o errexit
pytest -m "integration" --cov=src --cov=cli tests