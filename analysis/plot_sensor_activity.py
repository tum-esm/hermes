import colorsys
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
    "calibration",
    "air",
    "system",
    "wind",
    "enclosure",
]
LOG_TYPE = ["info", "warning", "error"]

DATA_TYPE_COLOR = {
    t: "#"
    + "".join(
        [
            hex(int(c * 255))[2:].zfill(2)
            for c in colorsys.hls_to_rgb((i * 12 / 360), 0.7, 0.8)
        ]
    )
    for i, t in enumerate(MEASUREMENT_TYPE + LOG_TYPE)
}
DATA_TYPE_OFFSET = {
    t: -round((i * 0.05) + (0.05 * math.floor(i / 5)), 2)
    for i, t in enumerate(MEASUREMENT_TYPE + LOG_TYPE)
}

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    sensor_number = 20
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
        for t in MEASUREMENT_TYPE:
            xs = grouped_measurements_df.get_column("timestamp")
            ys = [
                y + DATA_TYPE_OFFSET[t]
                for y in grouped_measurements_df.get_column(f"{t}_rpm")
            ]
            p.scatter(xs, ys, s=1, color=DATA_TYPE_COLOR[t], alpha=0.5)
        for t in LOG_TYPE:
            xs = grouped_logs_df.get_column("timestamp")
            ys = [
                y + DATA_TYPE_OFFSET[t] for y in grouped_logs_df.get_column(f"{t}_rpm")
            ]
            p.scatter(xs, ys, s=1.2, color=DATA_TYPE_COLOR[t], alpha=0.8)

    utils.save_plot(f"sensor_activity_{sensor_number}.png")
