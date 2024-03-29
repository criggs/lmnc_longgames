from typing import List
import pygame
import random
import numpy
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame


class MatrixDemo(MultiverseGame):
    def __init__(self, multiverse_displays):
        super().__init__("Matrix", 60, multiverse_displays)

        self.sim_height = int(self.height / self.upscale_factor)
        self.sim_width = int(self.width / self.upscale_factor)

        # Fire stuff
        self.fire_spawns = self.display_count + 1
        self.damping_factor = 0.98
        self.heat_amount = 4.0

        # Palette conversion, this is actually pretty nifty
        self.palette = numpy.array(
            [
                [0, 0, 0],
                [0, 20, 0],
                [0, 30, 0],
                [0, 160, 0],
                [0, 255, 0],
                [4, 31, 0],
                [40, 102, 0],
                [156, 199, 0],
                [235, 245, 0],
                [255, 255, 0],
                [255, 255, 0],
            ],
            dtype=numpy.uint8,
        )
        # FIIIREREEEEEEE
        self.matrix = numpy.zeros(
            (self.sim_height, self.sim_width), dtype=numpy.float32
        )

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
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()

        # Update the fire
        self.update()

        # Convert the fire buffer to RGB 888X (uint32 as four bytes)
        buf = self.matrix.clip(0.0, 1.0) * (len(self.palette) - 1)
        buf = numpy.rot90(buf)
        buf = buf.astype(numpy.uint8)
        buf = self.palette[buf]

        if self.upscale_factor != 1:
            # Upsample the sim to the windowed display
            buf = numpy.repeat(buf, self.upscale_factor, axis=1).repeat(
                self.upscale_factor, axis=0
            )

        # Update the displays from the buffer
        _2d_buf = pygame.surfarray.map_array(self.screen, buf)
        pygame.surfarray.blit_array(self.screen, _2d_buf)

    def reset(self):
        pass

    def fire_controller_input_event(self, event_id: int):
        event = pygame.event.Event(event_id)
        pygame.event.post(event)

    def update(self):
        self.matrix[:] *= 0.65

        for _ in range(10):
            x = random.randint(0, self.sim_width - 1)
            y = random.randint(0, self.sim_height // 2)
            self.matrix[y][x] = random.randint(128, 255) / 255.0

        # Propagate downwards
        old = self.matrix * 0.5
        self.matrix[:] = numpy.roll(self.matrix, 1, axis=0)
        self.matrix[:] += old
