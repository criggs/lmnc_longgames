import os

try:
    import RPi.GPIO as gpio
    print("Running on a Raspberry PI")
except (ImportError, RuntimeError):
    print("Not running on a Raspberry PI. Setting mock GPIO Zero Pin Factory.")
    os.environ["GPIOZERO_PIN_FACTORY"] = "mock"
    
from typing import Callable
from gpiozero import DigitalOutputDevice, Button
from time import sleep
from lmnc_longgames.constants import *


class ScreenPowerReset:
    def __init__(self, reset_pin: int, button_pin: int):
        self.power_reset = DigitalOutputDevice(reset_pin)
        self.button = Button(button_pin, bounce_time=BUTTON_BOUNCE_TIME_SEC)
        self.button.when_released = self.reset

    def reset(self):
        self.power_reset.on()
        sleep(1)
        self.power_reset.off()


def main():
    print("Resetting Screen Relay")
    r = ScreenPowerReset(reset_pin=PIN_RESET_RELAY, button_pin=16)
    r.reset()


if __name__ == "__main__":
    main()
