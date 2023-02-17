import colorsys
from datetime import timedelta
import math
from matplotlib import pyplot as plt
import polars as pl
from os.path import dirname
import os
from src import utils

PROJECT_DIR = dirname(os.path.abspath(__file__))
MEASUREMENT_DF_CACHE_PATH = os.path.join(
    PROJECT_DIR, "cache", "grouped_measurements_df.parquet"
)
LOGS_DF_CACHE_PATH = os.path.join(PROJECT_DIR, "cache", "grouped_logs_df.parquet")


MEASUREMENT_TYPE = [
    "co2",
    "air",
    "system",
    "wind",
    "enclosure",
]
LOG_TYPE = ["info", "warning", "error"]

DATA_TYPE_COLOR = {
    "co2": "#ef4444",  # red-500
    "air": "#f97316",  # orange-500
    "system": "#22c55e",  # green-500
    "wind": "#0f766e",  # teal-500
    "enclosure": "#1d4ed8",  # blue-500
    "info": "#22c55e",  # green-500
    "warning": "#f97316",  # orange-500
    "error": "#ef4444",  # red-500
}
MEASUREMENT_TYPE_OFFSET = {
    "co2": 0,
    "air": 0.045,
    "system": 0.015,
    "wind": -0.015,
    "enclosure": -0.045,
}
LOG_TYPE_OFFSET = {t: -round(i * 0.03, 2) for i, t in enumerate(LOG_TYPE)}

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    sensor_number = 3
    sensor_name = f"tum-esm-midcost-raspi-{sensor_number}"

    if (not os.path.exists(MEASUREMENT_DF_CACHE_PATH)) or (
        not os.path.exists(LOGS_DF_CACHE_PATH)
    ):
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

        grouped_measurements_df = measurements_df.groupby_dynamic(
            "timestamp", every="2m"
        ).agg(
            [
                ((pl.col("variant").filter(pl.col("variant") == t)).count()).alias(
                    f"{t}_rpm"
                )
                for t in MEASUREMENT_TYPE
            ]
        )
        grouped_logs_df = logs_df.groupby_dynamic("timestamp", every="2m").agg(
            [
                ((pl.col("severity").filter(pl.col("severity") == t)).count()).alias(
                    f"{t}_rpm"
                )
                for t in LOG_TYPE
            ]
        )

        grouped_measurements_df.write_parquet(MEASUREMENT_DF_CACHE_PATH)
        grouped_logs_df.write_parquet(LOGS_DF_CACHE_PATH)

    else:
        grouped_measurements_df = pl.read_parquet(MEASUREMENT_DF_CACHE_PATH)
        grouped_logs_df = pl.read_parquet(LOGS_DF_CACHE_PATH)

    print(grouped_measurements_df)
    print(grouped_logs_df)

    grouped_measurements_df = grouped_measurements_df.groupby_rolling(
        "timestamp", period=timedelta(minutes=30)
    ).agg([pl.col(f"{t}_rpm").mean() for t in MEASUREMENT_TYPE])

    # grouped_logs_df = grouped_logs_df.groupby_rolling(
    #    "timestamp", period=timedelta(minutes=5)
    # )

    plt.subplots(
        3,
        1,
        gridspec_kw={"height_ratios": [2, 2, 2], "hspace": 1},
        figsize=(12, 8),
    )

    with utils.plot(
        subplot_row_count=3,
        subplot_col_count=1,
        subplot_number=1,
        xlabel="UTC time",
        ylabel="code version with\nactive measurement data",
        title="CO2 Messages",
        xaxis_scale="days",
    ) as p:
        xs = grouped_measurements_df.get_column("timestamp")
        ys = [
            y + MEASUREMENT_TYPE_OFFSET["co2"]
            for y in grouped_measurements_df.get_column(f"co2_rpm")
        ]
        p.plot(
            xs, ys, linewidth=1.5, color=DATA_TYPE_COLOR["co2"], alpha=1, label="co2"
        )

    with utils.plot(
        subplot_row_count=3,
        subplot_col_count=1,
        subplot_number=2,
        xlabel="UTC time",
        ylabel="code version with\nactive measurement data",
        title="Other Measurement Messages",
        xaxis_scale="days",
    ) as p:
        for t in MEASUREMENT_TYPE:
            if t == "co2":
                continue
            xs = grouped_measurements_df.get_column("timestamp")
            ys = [
                y + MEASUREMENT_TYPE_OFFSET[t]
                for y in grouped_measurements_df.get_column(f"{t}_rpm")
            ]
            p.plot(xs, ys, linewidth=1.5, color=DATA_TYPE_COLOR[t], alpha=1, label=t)

    with utils.plot(
        subplot_row_count=3,
        subplot_col_count=1,
        subplot_number=3,
        xlabel="UTC time",
        ylabel="code version with\nactive measurement data",
        title="Log Messages",
        xaxis_scale="days",
    ) as p:
        for t in LOG_TYPE:
            xs = grouped_logs_df.get_column("timestamp")
            ys = [LOG_TYPE_OFFSET[t] for y in grouped_logs_df.get_column(f"{t}_rpm")]
            p.scatter(xs, ys, s=2.5, color=DATA_TYPE_COLOR[t], alpha=1, label=t)

    utils.save_plot(f"sensor_activity_{sensor_number}.png")
