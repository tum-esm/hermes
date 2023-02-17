import colorsys
import math


SENSOR_OFFSETS = {
    f"tum-esm-midcost-raspi-{i+1}": -round((i * 0.03) + (0.03 * math.floor(i / 5)), 2)
    for i in range(20)
}
SENSOR_COLORS = {
    f"tum-esm-midcost-raspi-{i+1}": "#"
    + "".join(
        [
            hex(int(c * 255))[2:].zfill(2)
            for c in colorsys.hls_to_rgb((i * 12 / 360), 0.7, 0.8)
        ]
    )
    for i in range(20)
}
