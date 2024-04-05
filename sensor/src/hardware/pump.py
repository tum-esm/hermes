import time

import gpiozero
import gpiozero.pins.pigpio

from src import utils, custom_types

PUMP_CONTROL_PIN_OUT = 19
PUMP_CONTROL_PIN_FREQUENCY = 10000
PUMP_SPEED_PIN_IN = 16


class PumpInterface:
    """Controls the pump SP 622 EC-BL from Schwarzer Precision via PWM."""

    def __init__(
        self,
        config: custom_types.Config,
        testing: bool = False,
        simulate: bool = False,
    ) -> None:
        self.logger = utils.Logger(
            origin="pump",
            print_to_console=testing,
            write_to_file=(not testing),
        )
        self.config = config
        self.simulate = simulate
        self.logger.info("Starting initialization")

        if self.simulate:
            self.logger.info("Simulating pump.")
            return
        # ---------------------------------------------------------------------
        # INITIALIZING THE PUMP CONTROL PIN

        # pin factory required for hardware PWM
        self.pin_factory = utils.get_gpio_pin_factory()

        # pins for setting desired pump speed
        self.control_pin = gpiozero.PWMOutputDevice(
            pin=PUMP_CONTROL_PIN_OUT,
            active_high=True,
            initial_value=0,
            frequency=PUMP_CONTROL_PIN_FREQUENCY,
            pin_factory=self.pin_factory,
        )

        # start pump to run continuously
        self.set_desired_pump_speed(
            pwm_duty_cycle=self.config.hardware.pump_pwm_duty_cycle,
        )
        time.sleep(0.5)

        self.logger.info("Finished initialization")

    def set_desired_pump_speed(
        self,
        pwm_duty_cycle: float,
    ) -> None:
        """sets the PWM duty cycle for the pump"""

        assert (
            0 <= pwm_duty_cycle <= 1
        ), f"pwm duty cycle has to be between 0 and 1 (passed {pwm_duty_cycle})"
        self.control_pin.value = pwm_duty_cycle

    def flush_system(self, duration: int, duty_cycle: float) -> None:
        """flushed the system by setting the pump to max speed and waiting the duration in seconds.
        At the end the pump speed is set to the duty cycle defined in the config file."""
        assert 0 <= duty_cycle <= 1
        self.set_desired_pump_speed(pwm_duty_cycle=duty_cycle)
        time.sleep(duration)
        self.set_desired_pump_speed(
            pwm_duty_cycle=self.config.hardware.pump_pwm_duty_cycle,
        )

    def teardown(self) -> None:
        """ends all hardware/system connections"""
        if self.simulate:
            return

        self.set_desired_pump_speed(pwm_duty_cycle=0)
        self.pin_factory.close()

        # I don't know why this is needed sometimes, just to make sure
        utils.run_shell_command(f"pigs w {PUMP_CONTROL_PIN_OUT} 0")
