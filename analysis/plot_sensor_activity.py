from src import utils

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    result = utils.SQLQueries.fetch_sensor_measurements(
        config, "tum-esm-midcost-raspi-20"
    )
    print(len(result))
    print(len(str(result)))
