import time
from src import utils, hardware

config = utils.ConfigInterface.read()
pump = hardware.PumpInterface(config)

for rps in [10, 20, 30, 40, 50, 60, 70]:
    print(f"setting rps to {rps}")
    pump.set_desired_pump_speed(unit="rps", value=rps)
    time.sleep(20)
