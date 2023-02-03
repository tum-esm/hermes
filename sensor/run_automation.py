import dotenv
import os
import filelock
from src import main

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    dotenv.load_dotenv(os.path.join(PROJECT_DIR, "config", ".env"))
    lock = filelock.FileLock(
        os.path.join(PROJECT_DIR, "run_automation.lock"),
        timeout=2,
    )

    try:
        with lock:
            main.run()
    except filelock.Timeout:
        raise TimeoutError("automation is already running")
