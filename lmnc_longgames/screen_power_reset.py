from typing import Callable
from gpiozero import DigitalOutputDevice, Button
from time import sleep

class ScreenPowerReset:
    def __init__(self,
                 reset_pin: int, 
                 button_pin: int):
        self.power_reset = DigitalOutputDevice(reset_pin)
        self.button = Button(button_pin)
        self.button.when_released = self.reset

    def reset(self):
        self.power_reset.on()
        sleep(1)
        self.power_reset.off()


def main():
    
    ScreenPowerReset(26, 16)
    while True:
        sleep(1)
        pass

if __name__ == "__main__":
    main()