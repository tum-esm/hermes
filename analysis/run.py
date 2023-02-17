import colorsys
import math
from matplotlib import pyplot as plt
from src import utils
import matplotlib.patches as mpatches

sensor_offsets = {
    f"tum-esm-midcost-raspi-{i+1}": -round((i * 0.03) + (0.03 * math.floor(i / 5)), 2)
    for i in range(20)
}
sensor_colors = {
    f"tum-esm-midcost-raspi-{i+1}": "#"
    + "".join(
        [
            hex(int(c * 255))[2:].zfill(2)
            for c in colorsys.hls_to_rgb((i * 12 / 360), 0.7, 0.8)
        ]
    )
    for i in range(20)
}

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
        xaxis_scale="months",
    ) as p:
        p.set_yticks(
            list(code_version_offsets.values()),
            list(code_version_offsets.keys()),
        )

        min_timestamp = min([a.first_measurement_timestamp for a in activities])
        max_timestamp = max([a.last_measurement_timestamp for a in activities])

        for code_version in code_version_offsets.keys():
            for sensor_name in sensor_offsets.keys():
                xs = [min_timestamp, max_timestamp]
                ys = [
                    code_version_offsets[code_version] + sensor_offsets[sensor_name]
                ] * 2
                p.plot(xs, ys, linewidth=5, color="#eeeeff")

        for a in activities:
            xs = [
                a.first_measurement_timestamp,
                a.last_measurement_timestamp,
            ]
            ys = [
                code_version_offsets[a.code_version] + sensor_offsets[a.sensor_name]
            ] * 2
            p.plot(xs, ys, linewidth=5, color=sensor_colors[a.sensor_name])

        patches = [mpatches.Patch(color=v, label=k) for k, v in sensor_colors.items()]
        p.legend(handles=patches, bbox_to_anchor=(1.02, 1))

    utils.save_plot("used_code_versions.png")
