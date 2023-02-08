import os
from utils import IP_LOGGER_DIR, AUTOMATION_DIR, AUTOMATION_VERSION

print("TESTING BASEROW-IP-LOGGER")
os.system(
    f"cd {IP_LOGGER_DIR} && .venv/bin/python run.py",
)

print("TESTING HERMES")
os.system(
    f"cd {AUTOMATION_DIR}/{AUTOMATION_VERSION} && "
    + '.venv/bin/python -m pytest -m "version_update"',
)

print("✨ DONE ✨")
