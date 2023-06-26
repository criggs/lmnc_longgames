from typing import List
import pygame
import random
import math
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.multiverse.multiverse_game import GameObject
from lmnc_longgames.constants import *
from pygame.locals import *

PALETTE = [
    (255,190,11),
    (251,86,7),
    (255,0,110),
    (205,66,255),
    (58,134,255)
]

# Game constants
INVADER_ROWS = 5
INVADER_GAP = 1
STARTING_LIVES = 5
INVADER_WIDTH = 3
INVADER_HEIGHT = 3
PLAYER_WIDTH = 3
PLAYER_HEIGHT = 3
    
class Invader(GameObject):
    def __init__(self, game, x, y):
        super().__init__(game)
        self.width = INVADER_WIDTH * game.upscale_factor
        self.height = INVADER_HEIGHT * game.upscale_factor
        self.x = x
        self.y = y
        
        self.color = random.choice(PALETTE)
        
    def update(self, dt, move_dir):
        super().update(dt)
        self.x += self.game.invader_speed * dt * move_dir
        if self.x <= 0:
            self.x = 0
            self.game.invader_shift = True
        if self.x >= self.game.width - self.width - 1:
            self.game.invader_shift = True
            self.x = self.game.width - self.width - 1
        #TODO if it hits the player, Game Over
            
    
    def move_down(self):
        self.y += self.height + INVADER_GAP * self.game.upscale_factor
        #TODO If it reaches the bottom, Game Over

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self._rect)
    
    def fire(self):
        #TODO Fire random invaders if they're on the bottom most position in their column. Probably need to keep track of a 'rank' list of each column
        pass

class Player(GameObject):
    def __init__(self, game):
        super().__init__(game)
        self.width = PLAYER_WIDTH * game.upscale_factor
        self.height = PLAYER_HEIGHT * game.upscale_factor
        self.x =  int((game.width / 2) - (self.width / 2))
        self.y = game.height - self.height
        self.speed = 5
        
        self.color = random.choice(PALETTE)
    
    def move(self, move_amount):
        self.x += self.speed * move_amount * self.game.upscale_factor
        if self.x + self.width >= self.game.width - 1:
            self.x = self.game.width - 1 - self.width
        if self.x <= 0:
            self.x = 0
    
    def update(self, dt):
        super().update(dt)
        
        #TODO Move

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self._rect)
        
    def fire(self):
        bullet = PlayerBullet(self.game, self.x + self.width // 2, self.y)
        self.game.player_bullets.append(bullet)
    


class PlayerBullet(GameObject):
    def __init__(self, game, x, y):
        super().__init__(game)
        self.width = 1 * game.upscale_factor
        self.height = 1 * game.upscale_factor
        self.speed = 20
        self.x = x
        self.y = y
        
        
    def update(self, dt: float):
        super().update(dt)
        self.y -= dt * self.speed * self.game.upscale_factor
        
    
    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self._rect)
        tail_rect = pygame.Rect(self.x, self.y + self.height, self.width, self.height * 2)
        pygame.draw.rect(screen, (150,150,150), tail_rect)
        tail_rect.y += tail_rect.height
        pygame.draw.rect(screen, (50,50,50), tail_rect)
           

class InvadersGame(MultiverseGame):
    '''
    It's space invaders!
    '''
    def __init__(self, multiverse_display):
        super().__init__("Invaders", 120, multiverse_display)
        self.invaders = []
        self.player_bullets = []
        self.invader_bullets = []
        self.invader_shift = False
        self.invader_move_dir = 1
        self.invader_speed = 0
        self.reset()

    def reset(self):
        self.game_over = False
        self.invaders = []
        self.player_bullets = []
        self.invader_bullets = []
        self.invader_shift = False
        self.invader_move_dir = 1
        self.invader_speed = 20
        gap = INVADER_GAP * self.upscale_factor
        width = INVADER_WIDTH * self.upscale_factor
        height = INVADER_HEIGHT * self.upscale_factor
        columns = len(self.multiverse_display.multiverse.displays) * 2
        for row in range(INVADER_ROWS):
            for column in range(columns):
                x = column * (width + gap) + gap
                y = row * (height + gap) + gap
                invader = Invader(self, x, y)
                self.invaders.append(invader)
        self.player = Player(self)

    def loop(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independence.
        """

        for event in events:
            if event.type == ROTATED_CW and event.controller == P1:
                self.player.move(1)
            if event.type == ROTATED_CCW and event.controller == P1:
                self.player.move(-1)
            if event.type == BUTTON_PRESSED and event.controller == P1 and event.input in [BUTTON_A] or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                #Fire
                self.player.fire()
            if self.game_over and event.type == BUTTON_RELEASED and event.controller == P1 and event.input in [BUTTON_A]:
                self.reset()
                return
            if self.game_over and event.type == BUTTON_RELEASED and event.controller == P1 and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()
                return
                

        keys = pygame.key.get_pressed()
        if keys[K_RIGHT]:
            self.player.move(1 / 5)
        elif keys[K_LEFT]:
            self.player.move(-1 / 5)

        self.screen.fill(BLACK)

        if self.game_over:
            text = self.font.render("YOU DIED", False, (135, 0, 0))
            if all(not invader.is_visible for invader in self.invaders):
                text = self.font.render("YOU WON", False, (135, 135, 0))
            text = pygame.transform.scale_by(text, self.upscale_factor)
            text_x = (self.width // 2) - (text.get_width() // 2)
            text_y = (self.height // 2) - (text.get_height() // 2)
            self.screen.blit(text, (text_x, text_y))
        else:
            for invader in self.invaders:
                invader.update(dt, self.invader_move_dir)

            if self.invader_shift:
                self.invader_shift = False
                self.invader_move_dir = -self.invader_move_dir
                for invader in self.invaders:
                    invader.move_down()
                self.invader_speed += 5
            
            for bullet in self.player_bullets:
                bullet.update(dt)
            
            for bullet in self.invader_bullets:
                bullet.update(dt)
                
            hit_bullets = []
            hit_invaders = []
            # Bullet collisions with invaders
            for bullet in self.player_bullets:
                for invader in self.invaders:
                    if bullet.collides_with(invader):
                        #Invader Hit!
                        hit_bullets.append(bullet)
                        hit_invaders.append(invader)
            
            self.player_bullets = [b for b in self.player_bullets if b not in hit_bullets]
            self.invaders = [i for i in self.invaders if i not in hit_invaders]
            
            
            # Check if all invaders are cleared
            if len(self.invaders) == 0:
                self.game_over = True
                return

            # Draw the things
            for bullet in self.player_bullets:
                bullet.draw(self.screen)
            
            for bullet in self.invader_bullets:
                bullet.draw(self.screen)
                
            self.player.draw(self.screen)
            for invader in self.invaders:
                invader.draw(self.screen)


