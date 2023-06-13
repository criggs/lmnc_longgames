from typing import Callable
from gpiozero import RotaryEncoder, Button
from time import sleep
from lmnc_longgames.constants import *


class RotaryEncoderController:
    def __init__(
        self,
        controller_id: int,
        event_callback: Callable[[int, int], None],
        clk_pin: int,
        dt_pin: int,
        rotary_push_button_pin: int,
        a_button_pin: int,
        b_button_pin: int,
    ):
        self.controller_id = controller_id
        self.event_callback = event_callback

        self.rotary_encoder = RotaryEncoder(clk_pin, dt_pin, max_steps=0)
        self.rotary_encoder.when_rotated_clockwise = self.build_callback(
            ROTATED_CW, ROTARY_PUSH
        )
        self.rotary_encoder.when_rotated_counter_clockwise = self.build_callback(
            ROTATED_CCW, ROTARY_PUSH
        )

        self.rotary_push = Button(rotary_push_button_pin)
        self.rotary_push.when_released = self.build_callback(
            BUTTON_RELEASED, ROTARY_PUSH
        )
        self.rotary_push.when_pressed = self.build_callback(BUTTON_PRESSED, ROTARY_PUSH)

        self.button_a = Button(a_button_pin)
        self.button_a.when_released = self.build_callback(BUTTON_RELEASED, BUTTON_A)
        self.button_a.when_pressed = self.build_callback(BUTTON_PRESSED, BUTTON_A)

        self.button_b = Button(b_button_pin)
        self.button_b.when_released = self.build_callback(BUTTON_RELEASED, BUTTON_B)
        self.button_b.when_pressed = self.build_callback(BUTTON_PRESSED, BUTTON_B)

    def build_callback(self, event_id, input_id):
        def callback():
            self.event_callback(event_id, self.controller_id, input_id)

        return callback


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
