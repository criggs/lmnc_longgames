import os
import platform
import logging

if platform.machine() != 'aarch64':
    logging.info("Not running on a Raspberry PI. Setting mock GPIO Zero Pin Factory.")
    os.environ["GPIOZERO_PIN_FACTORY"] = "mock"

    
import sys
from gpiozero import Button
from lmnc_longgames.constants import *


class ExitButton:
    def __init__(self, button_pin: int):
        self.button = Button(button_pin, bounce_time=BUTTON_BOUNCE_TIME_SEC)
        self.button.when_released = self.exit

    def exit(self):
        logging.info("Exiting from button press")
        os._exit(0)

def main():
    print("Resetting Screen Relay")
    r = ExitButton(button_pin=16)
    r.exit()


if __name__ == "__main__":
    main()
