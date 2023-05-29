from typing import Callable
from gpiozero import RotaryEncoder, Button
from time import sleep

class RotaryEncoderController:
    def __init__(self, 
                 event_callback: Callable[[int,int], None], 
                 positive_event_id: int = 1, 
                 negative_event_id: int = -1, 
                 clk_pin: int = 22, 
                 dt_pin: int = 27, 
                 button_pin: int = 17):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.button_pin = button_pin
        self.event_callback = event_callback
        self.positive_event_id = positive_event_id
        self.negative_event_id = negative_event_id
        self.rotary_encoder = RotaryEncoder(self.clk_pin, self.dt_pin, max_steps=0)
        self.rotary_encoder.when_rotated_clockwise = self.rotated_cw
        self.rotary_encoder.when_rotated_counter_clockwise = self.rotated_ccw
        self.button = Button(button_pin)

        self.running = False

    def rotated_cw(self):
        self.event_callback(self.positive_event_id)

    def rotated_ccw(self):
        self.event_callback(self.negative_event_id)


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