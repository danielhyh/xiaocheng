"""hardware-wiring.md 中板级映射的防回归测试。"""

import os

os.environ.setdefault("XIAOCHENG_MOCK", "1")

from app import config


def test_pca9685_channels_match_current_wiring_plan():
    channels = {
        config.SERVO_FRONT_PAN_CHANNEL,
        config.SERVO_FRONT_TILT_CHANNEL,
        config.SERVO_SCAN_CHANNEL,
        config.SERVO_REAR_PAN_CHANNEL,
        config.SERVO_REAR_TILT_CHANNEL,
    }

    assert channels == {0, 1, 2, 3, 4}
    assert config.LED_LEFT_CHANNEL is None
    assert config.LED_RIGHT_CHANNEL is None


def test_40_pin_gpio_assignments_are_current_and_unique():
    ultrasonic = {
        config.US_FRONT_TRIG,
        config.US_FRONT_ECHO,
        config.US_REAR_TRIG,
        config.US_REAR_ECHO,
    }
    motor_direction = {
        config.LEFT_IN1,
        config.LEFT_IN2,
        config.RIGHT_IN3,
        config.RIGHT_IN4,
    }

    assert ultrasonic == {19, 20, 23, 25}
    assert config.HEADLIGHT_PHYSICAL_PIN == 33
    assert config.HEADLIGHT_WPI_PIN == 22
    assert config.HEADLIGHT_PWM_OVERLAY == "pwm15-m2"
    assert ultrasonic.isdisjoint(motor_direction | {config.HEADLIGHT_WPI_PIN})
