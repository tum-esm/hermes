set -o errexit
pytest -m "ci" --cov=src --cov=cli tests