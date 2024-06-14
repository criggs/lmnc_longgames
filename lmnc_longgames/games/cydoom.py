"""
 Copyright(C) 2024 Wojciech Graj
 Copyright(C) 2024 Miika Lönnqvist

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License
 as published by the Free Software Foundation; either version 2
 of the License, or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
"""

from typing import List
import sys
from typing import Optional, Tuple


import cydoomgeneric as cdg
import numpy as np
import pygame

from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.constants import *
from multiprocessing import Process, Pipe, Queue, current_process, freeze_support
from queue import Empty, Full

keymap = {
    pygame.K_LEFT: cdg.Keys.LEFTARROW,
    pygame.K_RIGHT: cdg.Keys.RIGHTARROW,
    pygame.K_UP: cdg.Keys.UPARROW,
    pygame.K_DOWN: cdg.Keys.DOWNARROW,
    pygame.K_COMMA: cdg.Keys.STRAFE_L,
    pygame.K_PERIOD: cdg.Keys.STRAFE_R,
    pygame.K_LCTRL: cdg.Keys.FIRE,
    pygame.K_SPACE: cdg.Keys.USE,
    pygame.K_RSHIFT: cdg.Keys.RSHIFT,
    pygame.K_RETURN: cdg.Keys.ENTER,
    pygame.K_ESCAPE: cdg.Keys.ESCAPE,
}

screen_width = 143
screen_height = 53

class DoomRunner:

    def run_doom(self, resx, resy, output_pipe, input_queue: Queue):
        self.pixel_pipe = output_pipe
        self.key_queue = input_queue
        cdg.init(resx,
            resy,
            self.draw_frame,
            self.get_key)
        cdg.main()

    def draw_frame(self, pixels: np.ndarray) -> None:
        #print('draw_frame in DoomRunner class called')
        print(f'in doom - closed:{self.pixel_pipe.closed}, readable:{self.pixel_pipe.readable}, writeable:{self.pixel_pipe.writable}')
        
        self.pixel_pipe.send(pixels)

    def get_key(self) -> Optional[Tuple[int, int]]:
        try:
            key = self.key_queue.get(block=False)
            #print(f'get_key = {key}')
            return key
        except Empty:
            return None


class Cydoom(MultiverseGame):
    def __init__(self, multiverse_display):
        # TODO: Make 60+ FPS
        super().__init__("Doom", 30, multiverse_display)
        self.resx = screen_width * 4
        self.resy = screen_height * 4
        self.screen_pixels = None
        self.start_doom()

    def loop(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independence.
        """
        super().loop(events, dt)
        print(f'closed:{self.pixels_parent_conn.closed}, readable:{self.pixels_parent_conn.readable}, writeable:{self.pixels_parent_conn.writable}')
        pixels = self.pixels_parent_conn.recv()
        pixels = np.rot90(pixels)
        pixels = np.flipud(pixels)
        pixels = pixels[::4,::4]
        # Array must match surface dimensions
        if self.upscale_factor != 1:
            # Upsample the sim to the windowed display
            pixels = np.repeat(pixels, self.upscale_factor, axis=1).repeat(
                self.upscale_factor, axis=0
            )
        
        pygame.surfarray.blit_array(self.screen, pixels[:,:,[2,1,0]])
        #print(f'Done updating screen from cydoom loop')
        
        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()
            try:
                if event.type == pygame.KEYDOWN:
                    if event.key in keymap:
                        self.key_queue.put((1, keymap[event.key]))
                
                if event.type == pygame.KEYUP:
                    if event.key in keymap:
                        self.key_queue.put((0, keymap[event.key]))

                if event.type == BUTTON_PRESSED or event.type == BUTTON_RELEASED:
                    send = 1 if event.type == BUTTON_PRESSED else 0
                    if event.controller == P1 and event.input in [BUTTON_A]:
                        self.key_queue.put((send, cdg.Keys.FIRE))
                    
                    if event.controller == P1 and event.input in [ROTARY_PUSH]:
                        self.key_queue.put((send, cdg.Keys.USE))
                    
                    if event.controller == P1 and event.input in [BUTTON_B]:
                        self.key_queue.put((send, cdg.Keys.UPARROW))

                if event.type == ROTATED_CCW and event.controller == P1:
                    self.key_queue.put((1, cdg.Keys.LEFTARROW))
                    self.key_queue.put((0, cdg.Keys.LEFTARROW))

                if event.type == ROTATED_CW and event.controller == P1:
                    self.key_queue.put((1, cdg.Keys.RIGHTARROWs))
                    self.key_queue.put((0, cdg.Keys.RIGHTARROWs))

            except Full:
                print('Queue was full')
                
        #return None
        #pygame.display.flip()

    def reset(self):
        super().reset()
        self.teardown()
        self.start_doom()

    def teardown(self):
        self.doom_process.kill()
        print('killed Doom')
        super().teardown()


    def start_doom(self):
        print('Starting Doom')
        doom_class = DoomRunner()
        self.pixels_parent_conn, self.pixels_child_conn = Pipe(False)
        self.key_queue = Queue()
        self.doom_process = Process(target=doom_class.run_doom, args=(self.resx, self.resy, self.pixels_child_conn, self.key_queue))
        self.doom_process.start()


    def set_window_title(self, t: str) -> None:
        pass
