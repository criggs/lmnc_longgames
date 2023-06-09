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
import colorsys
import numpy
import time
from multiverse_game import MultiverseGame
from rotary_encoder_controller import RotaryEncoderController
from screen_power_reset import ScreenPowerReset

"""

"""

class LifeDemoGame(MultiverseGame):
    def __init__(self, multiverse_displays):
        super().__init__("Conway's Game of Life", 60, multiverse_displays)
        
        self.initial_life = 200 * self.display_count       # Number of live cells to seed
        self.GENERATION_TIME = 0.1     # MS between generations
        self.MINIMUM_LIFE = self.initial_life / 5       # Auto reseed when only this many alive cells remain
        self.SMOOTHED = True           # Enable for a more organic if somewhat unsettling feel

        self.DECAY = 0.95              # Rate at which smoothing effect decays, higher number = more persistent, 1.0 = no decay
        self.TENACITY = 32             # Rate at which smoothing effect increases

        # Palette conversion, this is actually pretty nifty
        self.palette = numpy.fromiter(self.build_palette(), dtype=numpy.uint8).reshape((256, 3))
        
        self.life = numpy.zeros((self.height, self.width), dtype=numpy.uint8)
        self.next_generation = numpy.zeros((self.height, self.width), dtype=numpy.uint8)
        self.neighbours = numpy.zeros((self.height, self.width), dtype=numpy.uint8)
        self.duration = numpy.zeros((self.height, self.width), dtype=numpy.float64)
        self.last_gen = time.time()
        
        self.seed_life()
        
    def build_palette(self, offset=0.1):
        for h in range(256):
            for c in colorsys.hsv_to_rgb(offset + h / 1024.0, 1.0, h / 255.0):
                yield int(c * 255)
            
    def seed_life(self):

        hsv_offset = random.randint(0, 360) / 360.0

        self.palette = numpy.fromiter(self.build_palette(hsv_offset), dtype=numpy.uint8).reshape((256, 3))
        for _ in range(self.initial_life):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.life[y][x] = int(True)  # Avoid: TypeError: 'bool' object isn't iterable

   
    def game_mode_callback(self, game_mode):    
        """
        Called when a game mode is selected
        
        Parameters:
            game_mode: The selected game mode
        """

    def loop(self, events: List, dt: float):
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
        buf = numpy.clip(self.duration.round(0), 0, 255).astype(numpy.uint8)
        buf = numpy.rot90(buf)
        buf = buf.astype(numpy.uint8)
        buf = self.palette[buf]

        # Update the displays from the buffer
        _2d_buf = pygame.surfarray.map_array(self.screen, buf)
        pygame.surfarray.blit_array(self.screen, _2d_buf)


    def reset(self):
        pass

    def fire_controller_input_event(self, event_id: int):
        event = pygame.event.Event(event_id)
        pygame.event.post(event)

    def update(self):

        self.duration[:] += self.life * self.TENACITY
        self.duration[:] *= self.DECAY

        if time.time() - self.last_gen < self.GENERATION_TIME:
            return

        self.last_gen = time.time()

        if numpy.sum(self.life) < self.MINIMUM_LIFE:
            self.seed_life()
            return

        # Rollin' rollin' rollin.
        _N = numpy.roll(self.life, -1, axis=0)
        _NW = numpy.roll(_N, -1, axis=1)
        _NE = numpy.roll(_N, 1, axis=1)
        _S = numpy.roll(self.life, 1, axis=0)
        _SW = numpy.roll(_S, -1, axis=1)
        _SE = numpy.roll(_S, 1, axis=1)
        _W = numpy.roll(self.life, -1, axis=1)
        _E = numpy.roll(self.life, 1, axis=1)

        # Compute the total neighbours for each cell
        self.neighbours[:] = _N + _NW + _NE + _S + _SW + _SE + _W + _E

        self.next_generation[:] = self.life[:]

        # Any cells with exactly three neighbours should always stay alive
        self.next_generation[:] += self.neighbours[:] == 3

        # Any alive cells with less than two neighbours should die
        self.next_generation[:] -= (self.neighbours[:] < 2) * self.life

        # Any alive cells with more than three neighbours should die
        self.next_generation[:] -= (self.neighbours[:] > 3) * self.life

        self.life[:] = numpy.clip(self.next_generation, 0, 1)

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

    game = LifeDemoGame(upscale_factor, headless = not show_window)

    ScreenPowerReset(reset_pin=26, button_pin=16)
    game_thread = Thread(target=game.run, args=[])

    game_thread.start()
    game_thread.join()


if __name__ == "__main__":
    main()


