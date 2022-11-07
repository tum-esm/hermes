import RPi.GPIO as GPIO
import time
import pigpio


PUMP_SPEED_CONTROL = 19
FREQUENCY = 10000

# The value is the result of a measurement between duty cycle and input speed
PUMP_SPEED_TO_DUTY_CYCLE_FACTOR = 1.344973917 * 10000

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme

GPIO.setup(PUMP_SPEED_CONTROL, GPIO.OUT)

print("setting up gpio connection")
pi = pigpio.pi("127.0.0.1", 8888)
assert pi.connected, 'pigpio is not connected, please run "sudo pigpiod -n 127.0.0.1"'


def set_pump_speed(speed: int) -> None:
    pi.hardware_PWM(
        PUMP_SPEED_CONTROL,
        FREQUENCY,
        int(speed * PUMP_SPEED_TO_DUTY_CYCLE_FACTOR),
    )


for s in [10, 30, 50, 70]:
    print(f"setting pump speed to {s}")
    set_pump_speed(s)
    time.sleep(2)

print("stopping pump")
set_pump_speed(0)

print("waiting 2 seconds")
time.sleep(2)

# I don't know what this line does but when I remove
# it, the pump doesn't work when running the script again
print("resetting pwm dutycycle")
pi.set_PWM_dutycycle(PUMP_SPEED_CONTROL, 0)

print("tearing down gpio connection")
pi.stop()
