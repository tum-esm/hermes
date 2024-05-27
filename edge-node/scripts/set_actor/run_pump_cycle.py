import time
from src import utils, hardware

config = utils.ConfigInterface.read()
pump = hardware.PumpInterface(config)

for duty_cycle in [0, 0.05, 0.1, 0.15, 0.2, 0]:
    print(f"setting rps to {duty_cycle}")
    pump.set_desired_pump_speed(pwm_duty_cycle=duty_cycle)
    time.sleep(20)

pump.teardown()
