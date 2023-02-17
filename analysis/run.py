from src import utils

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    print(utils.SQLQueries.fetch_sensor(config))
    print(utils.SQLQueries.fetch_sensor_code_version_activity(config))
