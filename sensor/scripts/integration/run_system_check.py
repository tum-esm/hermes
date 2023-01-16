from os.path import dirname, abspath, join
import sys
import time
import dotenv

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)
from src import utils, procedures

# .env file is helpful on development machines
dotenv.load_dotenv(join(PROJECT_DIR, "config", ".env"))

config = utils.ConfigInterface.read()
utils.SendingMQTTClient.init_sending_loop_process()

system_check_procedure = procedures.SystemCheckProcedure(config)
system_check_procedure.run()
