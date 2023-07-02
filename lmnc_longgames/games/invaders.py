from typing import List
import pygame
import random
import os
import math
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.multiverse.multiverse_game import GameObject
from lmnc_longgames.constants import *
from pygame.locals import *

script_path = os.path.realpath(os.path.dirname(__file__))

PALETTE = [
    (238, 85, 238),
    (229, 229, 56),
    (44, 247, 2),
    (81, 117, 225),
]

# Game constants
INVADER_ROWS = 4
INVADER_GAP = 1
STARTING_LIVES = 5
INVADER_WIDTH = 5
INVADER_HEIGHT = 5
PLAYER_WIDTH = 5
PLAYER_HEIGHT = 4

def load_sprites(name, count):
    return [pygame.image.load(f"{script_path}/assets/{name}_{i}.png").convert_alpha() for i in range(count)]

IMG_INVADER_A = load_sprites(f"invader_a", 2)
IMG_INVADER_B = load_sprites(f"invader_b", 2)
IMG_INVADER_C = load_sprites(f"invader_c", 2)

IMG_INVADERS = [IMG_INVADER_A, IMG_INVADER_B, IMG_INVADER_C]

IMG_INVADER_BULLET = load_sprites("invader_bullet", 4)

IMG_INVADER_PLAYER = pygame.image.load(f"{script_path}/assets/invader_player.png").convert_alpha()

class Invader(GameObject):
    def __init__(self, game, x, y, color, images):
        super().__init__(game)
        self.width = INVADER_WIDTH * game.upscale_factor
        self.height = INVADER_HEIGHT * game.upscale_factor
        self.x = x
        self.y = y        
        self.color = color
        self.images = []
        for image in images:
            image = pygame.transform.scale_by(image, game.upscale_factor)
            pxar = pygame.PixelArray(image)
            pxar.replace(WHITE, self.color)
            del pxar
            self.images.append(image)
        #TODO replace color
        
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
        self.game.play_note(0, 105, release=1000, waveform=32)

    def draw(self, screen):
        #pygame.draw.rect(screen, self.color, self._rect)
        
        image = self.images[self.game.animation_index]
        
        screen.blit(image, (self.x, self.y))
    
    def fire(self):
        self.game.invader_bullets.append(InvaderBullet(self.game, self.x, self.y))
        self.game.random_note()
            
class Player(GameObject):
    def __init__(self, game):
        super().__init__(game)
        self.width = PLAYER_WIDTH * game.upscale_factor
        self.height = PLAYER_HEIGHT * game.upscale_factor
        self.x =  int((game.width / 2) - (self.width / 2))
        self.y = game.height - self.height
        self.speed = 5
        
        self.color = random.choice(PALETTE)
        self.image = pygame.transform.scale_by(IMG_INVADER_PLAYER, game.upscale_factor)
    
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
        screen.blit(self.image, (self.x, self.y))
        #pygame.draw.rect(screen, WHITE, self._rect)
        
    def fire(self):
        bullet = PlayerBullet(self.game, self.x + (PLAYER_WIDTH // 2) * self.game.upscale_factor, self.y)
        self.game.player_bullets.append(bullet)
        self.game.random_note()
    
class InvaderBullet(GameObject):
    def __init__(self, game, x, y):
        super().__init__(game)
        self.width = 3 * game.upscale_factor
        self.height = 5 * game.upscale_factor
        self.speed = 20
        self.x = x
        self.y = y
        self.frame_time = 100
        self.frame = 0
        self.next_frame = pygame.time.get_ticks() + self.frame_time
        self.images = [pygame.transform.scale_by(image, game.upscale_factor) for image in IMG_INVADER_BULLET]
        
        
    def update(self, dt: float):
        super().update(dt)
        
        self.y += dt * self.speed * self.game.upscale_factor
        
    def draw(self, screen):
        now = pygame.time.get_ticks()
        if(self.next_frame < now):
            self.frame = (self.frame + 1) % len(IMG_INVADER_BULLET)
            self.next_frame = now + self.frame_time
        
        screen.blit(self.images[self.frame], (self.x, self.y))

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
        if self.y > self.game.height:
            self.game.invader_bullets.remove(self)
        
    
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
        self.animation_index = 0
        self.next_animation_tick = 0
        self.reset()

    def reset(self):
        self.game_over = False
        self.invaders = []
        self.player_bullets = []
        self.invader_bullets = []
        self.invader_shift = False
        self.invader_move_dir = 1
        self.invader_speed = 20
        self.animation_index = 0
        self.next_animation_tick = 0
        gap = INVADER_GAP * self.upscale_factor
        width = INVADER_WIDTH * self.upscale_factor
        height = INVADER_HEIGHT * self.upscale_factor
        columns = len(self.multiverse_display.multiverse.displays)
        for row in range(INVADER_ROWS):
            row_color = PALETTE[row]
            for column in range(columns):
                x = column * (width + gap) + gap
                y = row * (height + gap) + gap
                invader = Invader(self, x, y, row_color, IMG_INVADERS[row % 3])
                self.invaders.append(invader)
        self.player = Player(self)

    def loop(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independence.
        """
        now_ticks = pygame.time.get_ticks()
        invader_fire = False
        if self.next_animation_tick < pygame.time.get_ticks():
            self.animation_index = (self.animation_index + 1) % 2
            self.next_animation_tick = now_ticks + 1000
            invader_fire = True
            

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
            if len(self.invaders) == 0:
                text = self.font.render("YOU WON", False, (135, 135, 0))
            else:
                text = self.font.render("YOU DIED", False, (135, 0, 0))
            text = pygame.transform.scale_by(text, self.upscale_factor)
            text_x = (self.width // 2) - (text.get_width() // 2)
            text_y = (self.height // 2) - (text.get_height() // 2)
            self.screen.blit(text, (text_x, text_y))
        else:
            for invader in self.invaders:
                invader.update(dt, self.invader_move_dir)
                if invader._rect.bottom > self.player.y:
                    self.game_over = True
                    self.death_note()
                    return
            if len(self.invaders) > 0 and invader_fire:
                random.choice(self.invaders).fire()

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
            
            for bullet in self.invader_bullets:
                if bullet.collides_with(self.player):
                    #You Got Hit!
                    self.game_over = True
                    self.death_note()
                    return
            
            
            
            
            # Check if all invaders are cleared
            if not self.game_over and len(self.invaders) == 0:
                self.game_over = True
                self.win_note()
                return

            # Draw the things
            for bullet in self.player_bullets:
                bullet.draw(self.screen)
            
            for bullet in self.invader_bullets:
                bullet.draw(self.screen)
                
            self.player.draw(self.screen)
            for invader in self.invaders:
                invader.draw(self.screen)


