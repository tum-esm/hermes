import os
import sys
import time
import dotenv

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "config", ".env"))

sys.path.append(PROJECT_DIR)
from src import utils, procedures


if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    utils.MQTTConnection.validate_config()
    procedures.MessagingAgent.init(config)

    while True:
        procedures.MessagingAgent.check_errors()
        print(procedures.MessagingAgent.get_config_message())
        time.sleep(1)
