from matplotlib import pyplot as plt
from src import utils

sensor_offsets = {
    f"tum-esm-midcost-raspi-{i+1}": round(0.285 - (i * 0.03), 2) for i in range(20)
}

if __name__ == "__main__":
    config = utils.ConfigInterface.read()

    activities = utils.SQLQueries.fetch_sensor_code_version_activity(config)
    code_versions = list(set([a.code_version for a in activities]))
    code_version_offsets = {
        v: i
        for i, v in enumerate(
            list(sorted(code_versions, key=lambda v: int(v.split(".")[-1])))
        )
    }

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
        ylabel="used code version",
        legend="auto",
        title=r"User code version over time",
        xaxis_scale="months",
    ) as p:
        p.set_yticks(
            list(code_version_offsets.values()),
            list(code_version_offsets.keys()),
        )

        for a in activities:
            xs = [
                a.first_measurement_timestamp,
                a.last_measurement_timestamp,
            ]
            ys = [
                code_version_offsets[a.code_version] + sensor_offsets[a.sensor_name]
            ] * 2
            p.plot(
                xs,
                ys,
                linewidth=2,
                label=f"{a.sensor_name} {a.code_version}",
            )

    utils.save_plot("used_code_versions.png")
