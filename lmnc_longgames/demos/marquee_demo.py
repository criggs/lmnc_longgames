from typing import List
import os
import random
import pygame
import itertools
import logging
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame


script_path = os.path.realpath(os.path.dirname(__file__))


PALETTE = [
    (255,190,11),
    (251,86,7),
    (255,0,110),
    (205,66,255),
    (58,134,255),
    (155,93,229),
    (241,91,181),
    (254,228,64),
    (0,187,249),
    (0,245,212)
]

EXTRA_SPECIAL_THANKS = [
    "Dax",
    "Gadgetoid",
    "FineQuasar17",
    "TheEPROM9 LaTeX",
    "Chris Riggs"
]

SEPCIAL_THANKS_ADDITIONS = [
    "24 sausage and egg baguettees"
]

font = pygame.font.Font(f"{script_path}/../icl8x8u.bdf", 8)

"""

"""
class TextBox:
    
    def __init__(self, text, color, x, y, upscale_factor):
        
        self.text = text
        self.color = color
        self.x = x
        self.y = y
        self.upscale_factor = upscale_factor
        
        self.rendered_text = font.render(self.text, False, color)
        self.rendered_text = pygame.transform.scale_by(self.rendered_text, self.upscale_factor)
    
    @property
    def width(self):
        return self.rendered_text.get_width()
    
    @property
    def height(self):
        return self.rendered_text.get_height()
        
    def draw(self, screen):
        screen.blit(self.rendered_text, (int(self.x), int(self.y)))
        

class MarqueeDemo(MultiverseGame):

    def __init__(self, multiverse_displays, header_text):
        super().__init__("Marquee", 120, multiverse_displays)
        self.is_setup = False
        self.speed = 50
        self.row_a = []
        self.row_b = []
        self.row_c = []
        self.header_text = header_text
        self.header = None
        
    def setup(self):
        self.row_a = []
        self.row_b = []
        self.row_c = []
        self.header = TextBox(self.header_text, (135, 0, 135), 0, 1 * self.upscale_factor, self.upscale_factor)
        #Center It
        self.header.x = self.width / 2 - self.header.width / 2
            
        
        names_file = self.config.config.get("names_file", None)
        if names_file is not None:
            f = open(names_file, 'r')
            self.txt_lines = [stripped_name for name in f.readlines() if (stripped_name := name.strip()) != '']
        else:
            self.txt_lines = [f'Kosmo {i}' for i in range(35)]
        self.txt_lines += SEPCIAL_THANKS_ADDITIONS
        random.shuffle(self.txt_lines)
        random.shuffle(EXTRA_SPECIAL_THANKS)
        self.txt_lines = EXTRA_SPECIAL_THANKS + self.txt_lines
        logging.info(f'Starting Name Marquee with {len(self.txt_lines)} names')
            
    
    def update(self, dt):
        self.update_row(self.row_a, 15 * self.upscale_factor, dt)
        self.update_row(self.row_b, 27 * self.upscale_factor, dt)
        self.update_row(self.row_c, 39 * self.upscale_factor, dt)
         
    def update_row(self, row: list[TextBox], y, dt):
        # Move to the left
        pop_it = False
        for text_box in row:
            text_box.x = text_box.x - (self.speed * dt * self.upscale_factor)
            pop_it = text_box.x < -text_box.width
                
        if pop_it:
            row.pop(0)
            
        # Cha Cha now y'all
        
        # Add if empty
        if len(row) == 0 and len(self.txt_lines) > 0:
            text_box = TextBox(self.txt_lines.pop(0), random.choice(PALETTE), self.width, y, self.upscale_factor)
            row.append(text_box)
        gap = 0
        while len(row) > 0 and len(self.txt_lines) > 0 and row[-1].width + row[-1].x + (gap * self.upscale_factor) < self.width:
                separator_box = TextBox(" - ", (135, 0, 135), self.width, y, self.upscale_factor)
                row.append(separator_box)
                
                text_box = TextBox(self.txt_lines.pop(0), random.choice(PALETTE), self.width + separator_box.width, y, self.upscale_factor)
                row.append(text_box)
            

    def loop(self, events: List, dt: float):
        if not self.is_setup:
            self.setup()
            self.is_setup = True
            
        for event in events:
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()
        
        self.update(dt)
        
        if(len(self.row_a) == 0 and len(self.row_b) == 0 and len(self.row_c) == 0):
            self.reset()
        
        self.screen.fill(BLACK)
        
        self.header.draw(self.screen)

        for text_box in itertools.chain(self.row_a, self.row_b, self.row_c):
            text_box.draw(self.screen)


    def reset(self):
        self.setup()
