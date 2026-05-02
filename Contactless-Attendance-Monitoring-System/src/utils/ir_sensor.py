"""
utils/ir_sensor.py — KY-032 Infrared Sensor interface via Raspberry Pi GPIO.

The IR sensor detects when a candidate approaches the system and
triggers the camera + face recognition pipeline. When nobody is
in range, the system stays dormant (saves CPU on Pi).

Hardware:
    KY-032 IR Obstacle Avoidance Sensor Module
    Wiring: VCC → 5V (Pi pin 2), GND → GND (Pi pin 6), OUT → GPIO 17 (Pi pin 11)

Dependencies:
    RPi.GPIO (pre-installed on Raspberry Pi OS)
    pip3 install RPi.GPIO
"""

import sys
import time

try:
    import RPi.GPIO as GPIO
    RUNNING_ON_PI = True
except (ImportError, RuntimeError):
    # Not on a Raspberry Pi — use mock mode for development
    RUNNING_ON_PI = False
    print("[IR] WARNING: RPi.GPIO not available. Running in mock/simulation mode.")

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import IR_SENSOR_PIN


class IRSensor:
    """
    Interface for the KY-032 infrared obstacle avoidance sensor.

    The sensor outputs LOW (0) when an obstacle is detected (active low).
    """

    def __init__(self, pin: int = IR_SENSOR_PIN):
        self.pin = pin
        self._mock_triggered = False

        if RUNNING_ON_PI:
            GPIO.setmode(GPIO.BOARD)          # physical pin numbering
            GPIO.setup(self.pin, GPIO.IN)
            print(f"[IR] Sensor initialised on physical pin {self.pin}")
        else:
            print(f"[IR] Mock sensor on pin {self.pin} (simulation mode)")

    def is_triggered(self) -> bool:
        """
        Returns True when an obstacle/person is detected within range.
        KY-032 output is active LOW — GPIO reads 0 when triggered.
        """
        if RUNNING_ON_PI:
            return GPIO.input(self.pin) == GPIO.LOW
        else:
            # Simulation: auto-trigger after 3s for testing
            return self._mock_triggered

    def wait_for_trigger(self, poll_interval: float = 0.1, timeout: float = None) -> bool:
        """
        Block until the sensor is triggered or timeout expires.

        Args:
            poll_interval: seconds between checks
            timeout:       max seconds to wait (None = wait forever)

        Returns:
            True  if triggered
            False if timed out
        """
        start = time.time()
        print("[IR] Waiting for candidate to approach...")

        while True:
            if self.is_triggered():
                print("[IR] ✅ Person detected! Activating face recognition...")
                return True

            if timeout and (time.time() - start) > timeout:
                print("[IR] Timeout reached with no detection.")
                return False

            time.sleep(poll_interval)

    def wait_for_clear(self, poll_interval: float = 0.2) -> None:
        """Wait until the sensor is no longer triggered (person has moved away)."""
        while self.is_triggered():
            time.sleep(poll_interval)

    def cleanup(self):
        if RUNNING_ON_PI:
            GPIO.cleanup()
            print("[IR] GPIO cleaned up.")

    # ── Context manager support ────────────────────────────────────────────────
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
