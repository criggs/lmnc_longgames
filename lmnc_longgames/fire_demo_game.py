import sys, os

try:
    import RPi.GPIO as gpio
    print("Running on a Raspberry PI")
except (ImportError, RuntimeError):
    print("Not running on a Raspberry PI. Setting mock GPIO Zero Pin Factory.")
    os.environ["GPIOZERO_PIN_FACTORY"] = "mock"

from threading import Thread
import getopt
from typing import List
import pygame
import random
import numpy
from multiverse_game import MultiverseGame
from rotary_encoder_controller import RotaryEncoderController
from screen_power_reset import ScreenPowerReset

"""

"""

BYTES_PER_PIXEL = 4

class FireDemoGame(MultiverseGame):
    def __init__(self, upscale_factor, headless):
        super().__init__("Fire!!!", 80, upscale_factor, headless=headless)
        self.configure_display()
        self.screen = self.pygame_screen

        # Fire stuff
        self.fire_spawns = len(self.multiverse_display.displays) + 1
        self.damping_factor = 0.98
        self.heat_amount = 4.0

        # Palette conversion, this is actually pretty nifty
        self.palette = numpy.array([
            [0, 0, 0],
            [20, 20, 20],
            [180, 30, 0],
            [220, 160, 0],
            [255, 255, 180]
        ], dtype=numpy.uint8)
        # FIIIREREEEEEEE
        print(f"h: {self.height}, w: {self.width}")
        self.heat = numpy.zeros((self.height, self.width), dtype=numpy.float32)

   
    def game_mode_callback(self, game_mode):    
        """
        Called when a game mode is selected
        
        Parameters:
            game_mode: The selected game mode
        """

    def game_loop_callback(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independance.
        """
        for event in events:
            pass

        # Update the fire
        self.update()

        # Convert the fire buffer to RGB 888X (uint32 as four bytes)
        buf = self.heat.clip(0.0, 1.0) * 4
        buf = numpy.rot90(buf)
        buf = buf.astype(numpy.uint8)
        buf = self.palette[buf]

        # Update the displays from the buffer
        _2d_buf = pygame.surfarray.map_array(self.pygame_screen, buf)
        pygame.surfarray.blit_array(self.pygame_screen, _2d_buf)


    def reset_game_callback(self):
        pass

    def fire_controller_input_event(self, event_id: int):
        event = pygame.event.Event(event_id)
        pygame.event.post(event)

    # UPDATE THE FIIIIIIIIIIIIREEEEEEEEEEEEEEEEEEEEEEEEEE
    def update(self):
        # Clear the bottom two rows (off screen)
        self.heat[self.height - 1][:] = 0.0
        self.heat[self.height - 2][:] = 0.0

        # Add random fire spawns
        for c in range(self.fire_spawns):
            x = random.randint(0, self.width - 4) + 2
            self.heat[self.height - 1][x - 1:x + 1] = self.heat_amount / 2.0
            self.heat[self.height - 2][x - 1:x + 1] = self.heat_amount

        # Propagate the fire upwards
        a = numpy.roll(self.heat, -1, axis=0)  # y + 1, x
        b = numpy.roll(self.heat, -2, axis=0)  # y + 2, x
        c = numpy.roll(self.heat, -1, axis=0)  # y + 1
        d = numpy.roll(c, 1, axis=1)      # y + 1, x + 1
        e = numpy.roll(c, -1, axis=1)     # y + 1, x - 1

        # Average over 5 adjacent pixels and apply damping
        self.heat[:] += a + b + d + e
        self.heat[:] *= self.damping_factor / 5.0

def main():
    # Contants/Configuration
    show_window = False
    debug = False
    opts, args = getopt.getopt(sys.argv[1:],"hwd",[])
    for opt, arg in opts:
        if opt == '-h':
            print ('longpong.py [-w] [-d]')
            sys.exit()
        elif opt == '-w':
            show_window = True
        elif opt == '-d':
            debug = True
    
    upscale_factor = 1 if show_window else 1

    game = FireDemoGame(upscale_factor, headless = not show_window)

    ScreenPowerReset(reset_pin=26, button_pin=16)
    game_thread = Thread(target=game.run, args=[])

    game_thread.start()
    game_thread.join()


if __name__ == "__main__":
    main()


