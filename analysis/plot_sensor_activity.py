from matplotlib import pyplot as plt
import polars as pl
from src import utils

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    sensor_number = 20
    sensor_name = f"tum-esm-midcost-raspi-{sensor_number}"

    measurements = utils.SQLQueries.fetch_sensor_measurements(config, sensor_name)
    logs = utils.SQLQueries.fetch_sensor_logs(config, sensor_name)

    print(f"plotting activity of {sensor_name}")
    print(f"{len(measurements)} measurement(s)")
    print(f"{len(logs)} log(s)")

    measurements_df = pl.DataFrame(
        {
            "timestamp": [m.timestamp for m in measurements],
            "variant": [m.value.variant for m in measurements],
        }
    ).sort(by="timestamp")
    logs_df = pl.DataFrame(
        {
            "timestamp": [l.timestamp for l in logs],
            "severity": [l.severity for l in logs],
        }
    ).sort(by="timestamp")

    # print(measurements_df)
    # print(logs_df)

    measurement_data_type = ["co2", "calibration", "air", "system", "wind", "enclosure"]
    log_data_type = ["info", "warning", "error"]

    grouped_measurements_df = measurements_df.groupby_dynamic(
        "timestamp", every="2m"
    ).agg(
        [
            ((pl.col("variant").filter(pl.col("variant") == t)).count()).alias(
                f"{t}_rpm"
            )
            for t in measurement_data_type
        ]
    )
    grouped_logs_df = logs_df.groupby_dynamic("timestamp", every="2m").agg(
        [
            ((pl.col("severity").filter(pl.col("severity") == t)).count()).alias(
                f"{t}_rpm"
            )
            for t in log_data_type
        ]
    )

    # print(grouped_measurements_df)
    # print(grouped_logs_df)

    plt.subplots(
        1,
        1,
        gridspec_kw={"height_ratios": [2], "hspace": 0.5},
        figsize=(12, 6),
    )

    with utils.plot(
        subplot_row_count=1,
        subplot_col_count=1,
        subplot_number=1,
        xlabel="UTC time",
        ylabel="code version with\nactive measurement data",
        title="Used code version over time",
        xaxis_scale="days",
    ) as p:
        for t in measurement_data_type:
            xs = grouped_measurements_df.get_column("timestamp")
            ys = [y + 0 for y in grouped_measurements_df.get_column(f"{t}_rpm")]
            p.scatter(xs, ys, s=1, color="red", alpha=0.5)

    utils.save_plot(f"sensor_activity_{sensor_number}.png")
