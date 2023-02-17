from src import utils

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    result = utils.SQLQueries.fetch_sensor_measurements(
        config, "tum-esm-midcost-raspi-1"
    )
    print(len(result), len(str(result)))

    result = utils.SQLQueries.fetch_sensor_logs(config, "tum-esm-midcost-raspi-1")
    print(len(result), len(str(result)))
