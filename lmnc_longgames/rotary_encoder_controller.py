from typing import Callable
from gpiozero import RotaryEncoder, Button
from time import sleep

class RotaryEncoderController:
    def __init__(self, 
                 event_callback: Callable[[int,int], None], 
                 clk_pin: int, 
                 dt_pin: int, 
                 button_pin: int,
                 positive_event_id: int = 1, 
                 negative_event_id: int = -1,
                 button_pressed_id: int = 2,
                 button_released_id: int = 3):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.button_pin = button_pin
        self.event_callback = event_callback
        self.positive_event_id = positive_event_id
        self.negative_event_id = negative_event_id
        self.button_pressed_id = button_pressed_id
        self.button_released_id = button_released_id
        self.rotary_encoder = RotaryEncoder(self.clk_pin, self.dt_pin, max_steps=0)
        self.rotary_encoder.when_rotated_clockwise = self.rotated_cw
        self.rotary_encoder.when_rotated_counter_clockwise = self.rotated_ccw
        self.button = Button(button_pin)
        self.button.when_released = self.button_released
        self.button.when_pressed = self.button_pressed

    def rotated_cw(self):
        self.event_callback(self.positive_event_id)

    def rotated_ccw(self):
        self.event_callback(self.negative_event_id)
        
    def button_pressed(self):
        self.event_callback(self.button_pressed_id)
        
    def button_released(self):
        self.event_callback(self.button_released_id)


def main():
    def callback(event_id):
        print(f'{"increased" if event_id > 0 else "decreased"} encoder')

    controller = RotaryEncoderController(callback)
    while True:
        print(controller.rotary_encoder.steps)
        sleep(1)
        pass

if __name__ == "__main__":
    main()