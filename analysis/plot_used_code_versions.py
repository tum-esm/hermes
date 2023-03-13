from matplotlib import pyplot as plt
from src import utils
import matplotlib.patches as mpatches

if __name__ == "__main__":
    config = utils.ConfigInterface.read()

    activities = utils.SQLQueries.fetch_sensor_code_version_activity(config)
    code_versions = list(set([a.code_version for a in activities]))
    code_version_offsets = {
        v: i * 0.9
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
        ylabel="code version with\nactive measurement data",
        title="Used code version over time",
        xaxis_scale="days",
    ) as p:
        p.set_yticks(
            list(code_version_offsets.values()),
            list(code_version_offsets.keys()),
        )

        min_timestamp = min([a.first_timestamp for a in activities])
        max_timestamp = max([a.last_timestamp for a in activities])

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
                a.first_timestamp,
                a.last_timestamp,
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

    utils.save_plot("used_code_versions.png")
