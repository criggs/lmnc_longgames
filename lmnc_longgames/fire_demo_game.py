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
    def __init__(self, multiverse_displays):
        super().__init__("Fire!!!", 80, multiverse_displays)


        self.sim_height = int(self.height / self.upscale_factor)
        self.sim_width = int(self.width / self.upscale_factor)

        # Fire stuff
        self.fire_spawns = self.display_count + 1
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
        self.heat = numpy.zeros((self.sim_height, self.sim_width), dtype=numpy.float32)
        

   
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
        buf = self.heat.clip(0.0, 1.0) * 4
        buf = numpy.rot90(buf)
        buf = buf.astype(numpy.uint8)
        buf = self.palette[buf]
        
        if self.upscale_factor != 1:
            #Upsample the sim to the windowed display
            buf = numpy.repeat(buf, self.upscale_factor, axis=1).repeat(self.upscale_factor, axis=0)

        # Update the displays from the buffer
        _2d_buf = pygame.surfarray.map_array(self.screen, buf)
        pygame.surfarray.blit_array(self.screen, _2d_buf)


    def reset(self):
        pass

    def fire_controller_input_event(self, event_id: int):
        event = pygame.event.Event(event_id)
        pygame.event.post(event)

    # UPDATE THE FIIIIIIIIIIIIREEEEEEEEEEEEEEEEEEEEEEEEEE
    def update(self):
        # Clear the bottom two rows (off screen)
        self.heat[self.sim_height - 1][:] = 0.0
        self.heat[self.sim_height - 2][:] = 0.0

        # Add random fire spawns
        for c in range(self.fire_spawns):
            x = random.randint(0, self.sim_width - 4) + 2
            self.heat[self.sim_height - 1][x - 1:x + 1] = self.heat_amount / 2.0
            self.heat[self.sim_height - 2][x - 1:x + 1] = self.heat_amount

        # Propagate the fire upwards
        a = numpy.roll(self.heat, -1, axis=0)  # y + 1, x
        b = numpy.roll(self.heat, -2, axis=0)  # y + 2, x
        c = numpy.roll(self.heat, -1, axis=0)  # y + 1
        d = numpy.roll(c, 1, axis=1)      # y + 1, x + 1
        e = numpy.roll(c, -1, axis=1)     # y + 1, x - 1

        # Average over 5 adjacent pixels and apply damping
        self.heat[:] += a + b + d + e
        self.heat[:] *= self.damping_factor / 5.0

