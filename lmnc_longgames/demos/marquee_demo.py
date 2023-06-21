from typing import List
import pygame
import numpy
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame

"""

"""


class MarqueeDemo(MultiverseGame):

    def __init__(self, multiverse_displays):
        super().__init__("Marquee", 120, multiverse_displays)
        pass        


    def loop(self, events: List, dt: float):
        
        self.screen.fill(BLACK)

        text = self.font.render("TODO", False, (135, 0, 135))
        text = pygame.transform.scale_by(text, self.upscale_factor)
        text_x = (self.width // 2) - (text.get_width() // 2)
        text_y = (self.height // 2) - (text.get_height() // 2)
        self.screen.blit(text, (text_x, text_y))
            

    def reset(self):
        pass
