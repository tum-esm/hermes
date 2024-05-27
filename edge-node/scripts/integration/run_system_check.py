from os.path import dirname, abspath, join
import sys
import dotenv

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(PROJECT_DIR)
from src import utils, hardware, procedures

# .env file is helpful on development machines
dotenv.load_dotenv(join(PROJECT_DIR, "config", ".env"))

config = utils.ConfigInterface.read()
procedures.MQTTAgent.init(config)

hardware_interface = hardware.HardwareInterface(config)
procedures.SystemCheckProcedure(config, hardware_interface).run()
