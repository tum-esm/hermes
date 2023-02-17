from matplotlib import pyplot as plt
import polars as pl
from src import utils

if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    sensor_name = "tum-esm-midcost-raspi-20"

    measurements = utils.SQLQueries.fetch_sensor_measurements(config, sensor_name)
    logs = utils.SQLQueries.fetch_sensor_logs(config, sensor_name)

    print(f"plotting activity of {sensor_name}")
    print(f"{len(measurements)} measurement(s)")
    print(f"{len(logs)} log(s)")

    measurement_df = pl.DataFrame(
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

    print(measurement_df)
    # print(logs_df)

    grouped_measurement_df = measurement_df.groupby_dynamic(
        "timestamp", every="2m"
    ).agg(
        [
            (
                (pl.col("variant").filter(pl.col("variant") == "co2")).count() * 0.5
            ).alias("co2_rpm"),
            (
                (pl.col("variant").filter(pl.col("variant") == "calibration")).count()
                * 0.5
            ).alias("calibration_rpm"),
            (
                (pl.col("variant").filter(pl.col("variant") == "air")).count() * 0.5
            ).alias("air_rpm"),
            (
                (pl.col("variant").filter(pl.col("variant") == "system")).count() * 0.5
            ).alias("system_rpm"),
            (
                (pl.col("variant").filter(pl.col("variant") == "wind")).count() * 0.5
            ).alias("wind_rpm"),
            (
                (pl.col("variant").filter(pl.col("variant") == "enclosure")).count()
                * 0.5
            ).alias("enclosure_rpm"),
        ]
    )

    print(grouped_measurement_df)

    """
    plt.subplots(
        1,
        1,
        gridspec_kw={"height_ratios": [2], "hspace": 0.5},
        figsize=(20, 12),
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
        min_timestamp = min([a.first_measurement_timestamp for a in activities])
        max_timestamp = max([a.last_measurement_timestamp for a in activities])

        for code_version in code_version_offsets.keys():
            for sensor_name in utils.SENSOR_OFFSETS.keys():
                xs = [min_timestamp, max_timestamp]
                ys = [
                    code_version_offsets[code_version]
                    + utils.SENSOR_OFFSETS[sensor_name]
                ] * 2
                p.plot(xs, ys, linewidth=5, color="#e2e8f0")

        for a in activities:
            xs = [
                a.first_measurement_timestamp,
                a.last_measurement_timestamp,
            ]
            ys = [
                code_version_offsets[a.code_version]
                + utils.SENSOR_OFFSETS[a.sensor_name]
            ] * 2
            p.plot(xs, ys, linewidth=5, color=utils.SENSOR_COLORS[a.sensor_name])

        patches = [
            mpatches.Patch(color=v, label=k) for k, v in utils.SENSOR_COLORS.items()
        ]
        p.legend(handles=patches, bbox_to_anchor=(1.02, 1))

    utils.save_plot("used_code_versions.png")"""
