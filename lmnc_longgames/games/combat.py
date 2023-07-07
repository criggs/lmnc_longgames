from typing import List
import pygame
import random
import os
import math
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.multiverse.multiverse_game import GameObject
from lmnc_longgames.constants import *
from pygame.locals import *
from collections import namedtuple

script_path = os.path.realpath(os.path.dirname(__file__))


# Game constants
TANK_WIDTH = 5
TANK_HEIGHT = 5

def load_sprites(name, count):
    return [pygame.image.load(f"{script_path}/assets/{name}_{i}.png").convert_alpha() for i in range(count)]

TANK_A = load_sprites(f"tank_a", 8)
TANK_B = load_sprites(f"tank_b", 8)

Direction = namedtuple("Direction", "index x_dir y_dir")
N  = Direction(0,  0, -1)
NE = Direction(1,  1, -1)
E  = Direction(2,  1,  0)
SE = Direction(3,  1,  1)
S  = Direction(4,  0,  1)
SW = Direction(5, -1,  1)
W  = Direction(6, -1,  0)
NW = Direction(7, -1, -1)

Directions = [N,NE,E,SE,S,SW,W,NW]


class Player(GameObject):
    def __init__(self, game, player):
        super().__init__(game)
        self.width = TANK_WIDTH * game.upscale_factor
        self.height = TANK_HEIGHT * game.upscale_factor
        if player == P1:
            self.x =  0
            self.y = 0
            self.dir = E
            images = TANK_A
        else:
            self.x = game.width - self.width
            self.y = game.height - self.height
            self.dir = W
            images = TANK_B
        self.speed = 5
                
        self.images = [pygame.transform.scale_by(image, game.upscale_factor) for image in images]
    
    def move(self, move_amount):
        self.x += self.speed * move_amount * self.game.upscale_factor * self.dir.x_dir
        self.y += self.speed * move_amount * self.game.upscale_factor * self.dir.y_dir
        
        if self.x + self.width >= self.game.width - 1:
            self.x = self.game.width - 1 - self.width
        if self.x <= 0:
            self.x = 0
            
        if self.y + self.height >= self.game.height - 1:
            self.y = self.game.height - 1 - self.height
        if self.y <= 0:
            self.y = 0
            
    def rotate(self, amount):
        self.dir = Directions[(self.dir.index + amount) % len(Directions)]
            
    
    def update(self, dt):
        super().update(dt)
        #Not sure there's anything to do here

    def draw(self, screen):
        image = self.images[self.dir.index]
        screen.blit(image, (self.x, self.y))
        
    def fire(self):
        #TODO Fire based on dir
        bullet = Bullet(self.game, self._rect.centerx, self._rect.centery, self.dir)
        self.game.bullets.append(bullet)
        self.game.random_note()
    
class Bullet(GameObject):
    def __init__(self, game, x, y, dir: Direction):
        super().__init__(game)
        #TODO: Which player is this bullet from
        self.width = 1 * game.upscale_factor
        self.height = 1 * game.upscale_factor
        self.speed = 20
        self.x = x
        self.y = y
        self.dir = dir
        
        
    def update(self, dt: float):
        super().update(dt)
        
        self.x += dt * self.speed * self.game.upscale_factor * self.dir.x_dir
        self.y += dt * self.speed * self.game.upscale_factor * self.dir.y_dir
        
        if self.y > self.game.height or self.y < 0 or self.x > self.game.width or self.x < 0:
            self.game.bullets.remove(self)
        
    
    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self._rect)
           

class CombatGame(MultiverseGame):
    '''
    World of 8-bit tanks!
    '''
    def __init__(self, multiverse_display):
        super().__init__("Combat", 120, multiverse_display)
        self.invaders = []
        self.bullets = []
        self.reset()

    def reset(self):
        self.game_over = False
        self.bullets = []
        self.p1_tank = Player(self, P1)
        self.p2_tank = Player(self, P2)

    def loop(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independence.
        """
        now_ticks = pygame.time.get_ticks()

        for event in events:
            
            #Turn
            if (event.type == ROTATED_CW and event.controller == P1) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT):
                self.p1_tank.rotate(1)
            if (event.type == ROTATED_CCW and event.controller == P1) or (event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT):
                self.p1_tank.rotate(-1)
            if (event.type == ROTATED_CW and event.controller == P2) or (event.type == pygame.KEYDOWN and event.key == pygame.K_d):
                self.p2_tank.rotate(1)
            if (event.type == ROTATED_CCW and event.controller == P2) or (event.type == pygame.KEYDOWN and event.key == pygame.K_a):
                self.p2_tank.rotate(-1)
                
            # Fire
            if event.type == BUTTON_PRESSED and event.controller == P1 and event.input in [BUTTON_A] or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self.p1_tank.fire()
            if event.type == BUTTON_PRESSED and event.controller == P2 and event.input in [BUTTON_A] or (event.type == pygame.KEYDOWN and event.key == pygame.K_f):
                self.p2_tank.fire()

            #Move
            if event.type == BUTTON_PRESSED and event.controller == P1 and event.input in [BUTTON_B] or (event.type == pygame.KEYDOWN and event.key == pygame.K_UP):
                self.p1_tank.move(1)
            if event.type == BUTTON_PRESSED and event.controller == P2 and event.input in [BUTTON_B] or (event.type == pygame.KEYDOWN and event.key == pygame.K_w):
                self.p2_tank.move(1)
            
            # Reset/Quit
            if self.game_over and event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()
                return
            if self.game_over and event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()
                return
                

        self.screen.fill(BLACK)

        if self.game_over:
            if len(self.invaders) == 0:
                text = self.font.render("YOU WON", False, (135, 135, 0))
            else:
                text = self.font.render("YOU DIED", False, (135, 0, 0))
            text = pygame.transform.scale_by(text, self.upscale_factor)
            text_x = (self.width // 2) - (text.get_width() // 2)
            text_y = (self.height // 2) - (text.get_height() // 2)
            self.screen.blit(text, (text_x, text_y))
        else:

            
            for bullet in self.bullets:
                bullet.update(dt)
            
            #TODO Hit detection
            
            # Draw the things
            for bullet in self.bullets:
                bullet.draw(self.screen)
            
            self.p1_tank.draw(self.screen)
            self.p2_tank.draw(self.screen)


