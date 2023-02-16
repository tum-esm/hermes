import json
from src import utils

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    print(json.dumps(config.dict(), indent=4))
