from typing import List
import logging
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
WALL_COLOR = (150,150,150)

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

BULLET_DAMAGE = 10
PLAYER_HEALTH = 100


class Player(GameObject):
    def __init__(self, game, player):
        super().__init__(game)
        self.width = TANK_WIDTH * game.upscale_factor
        self.height = TANK_HEIGHT * game.upscale_factor
        self.player = player
        self.health = PLAYER_HEALTH
        
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
        self.speed = 10
        self.moving = False
                
        self.images = [pygame.transform.scale_by(image, game.upscale_factor) for image in images]
            
    def rotate(self, amount):
        self.dir = Directions[(self.dir.index + amount) % len(Directions)]
            
    
    def update(self, dt):
        super().update(dt)
        self.check_bullet_hits()
        if self.moving:
            
            orig_xy = (self.x, self.y)
            
            self.x += self.speed * self.game.upscale_factor * self.dir.x_dir * dt
            self.y += self.speed * self.game.upscale_factor * self.dir.y_dir * dt
            
            if self.x + self.width >= self.game.width - 1:
                self.x = self.game.width - 1 - self.width
            if self.x <= 0:
                self.x = 0
                
            if self.y + self.height >= self.game.height - 1:
                self.y = self.game.height - 1 - self.height
            if self.y <= 0:
                self.y = 0
             
            if self.collision_with_wall() or self.collision_with_other_player():
                self.x, self.y = orig_xy
            

    def check_bullet_hits(self):
        
        other_player = P2 if self.player == P1 else P1
        
        hits = set([bullet for bullet in self.game.bullets if bullet.player == other_player and self.collides_with(bullet)])
        
        if len(hits) > 0:
            logging.info(f"Player {self.player} hit!")
            self.game.death_note()
            
            #Remove bullet from list
            self.game.bullets.difference_update(hits)
            
            #Drop player health
            self.health -= len(hits) * BULLET_DAMAGE

    def collision_with_wall(self):
        for wall in self.game.walls:
            if self.collides_with(wall):
                return True
        return False
    
    def collision_with_other_player(self):
        other_player = self.game.p2_tank if self.player == P1 else self.game.p1_tank
        return self.collides_with(other_player)
        
    
    def draw(self, screen):
        image = self.images[self.dir.index]
        screen.blit(image, (self.x, self.y))
        
    def fire(self):
        bullet = Bullet(self.game, self._rect.centerx, self._rect.centery, self.dir, self.player)
        self.game.bullets.add(bullet)
        self.game.random_note()
    
class Bullet(GameObject):
    def __init__(self, game, x, y, dir: Direction, player):
        super().__init__(game)
        self.width = 1 * game.upscale_factor
        self.height = 1 * game.upscale_factor
        self.speed = 20
        self.x = x
        self.y = y
        self.dir = dir
        self.x_dir = dir.x_dir
        self.y_dir = dir.y_dir
        self.player = player
        self.bounce_count = 0
        
        
    def update(self, dt: float):
        super().update(dt)
        
        for wall in self.game.walls:
            if self.collide_wall(wall):
                self.bounce_count += 1
        
        self.x += dt * self.speed * self.game.upscale_factor * self.x_dir
        self.y += dt * self.speed * self.game.upscale_factor * self.y_dir
        
        if self.bounce_count > 3 or self.y > self.game.height or self.y < 0 or self.x > self.game.width or self.x < 0:
            self.game.bullets.remove(self)
            

        
    def collide_wall(self, wall: pygame.rect.Rect):
        # wall = wall.copy()
        # wall.heigh += 1
        # wall.width += 1
        collision_rect = self._rect.copy()
        collision_rect.height += 1
        collision_rect.width += 1
        if collision_rect.colliderect(wall):
            if wall.collidepoint(collision_rect.topleft) and wall.collidepoint(collision_rect.topright):
                #full top hit
                #send down
                self.y_dir = 1
            elif wall.collidepoint(collision_rect.bottomleft) and wall.collidepoint(collision_rect.bottomright):
                #full bottom hit
                #send up
                self.y_dir = -1
            elif wall.collidepoint(collision_rect.topright) and wall.collidepoint(collision_rect.bottomright):
                #full right hit
                #send left
                self.x_dir = -1
            elif wall.collidepoint(collision_rect.topleft) and wall.collidepoint(collision_rect.bottomleft):
                #full left hit
                #send right
                self.x_dir = 1    
            
            # Check for corner hits
            elif wall.collidepoint(collision_rect.topright):
                #corner hit, down and left
                self.y_dir = 1
                self.x_dir = -1
                # self.y = wall.bottom
                # self.x = wall.left - self.width
            elif wall.collidepoint(collision_rect.topleft):
                #corner hit, down and right
                self.y_dir = 1
                self.x_dir = 1
                # self.y = wall.bottom
                # self.x = wall.right
            elif wall.collidepoint(collision_rect.bottomleft):
                #corner hit, up and right
                self.y_dir = -1
                self.x_dir = 1
                # self.y = wall.top - self.height
                # self.x = wall.right
            elif wall.collidepoint(collision_rect.bottomright):
                #corner hit, up and left
                self.y_dir = -1
                self.x_dir = -1
                # self.y = wall.top - self.height
                # self.x = wall.left - self.width
            self.game.random_note(waveform=32)
            return True
        return False
    
    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self._rect)
           

class CombatGame(MultiverseGame):
    '''
    World of 8-bit tanks!
    '''
    def __init__(self, multiverse_display):
        super().__init__("Combat", 60, multiverse_display)
        self.bullets = set()
        self.walls = []
        self.reset()
        

    def reset(self):
        self.game_over = False
        self.bullets = set()
        self.p1_tank = Player(self, P1)
        self.p2_tank = Player(self, P2)
        self.walls = []
        
        # Build the walls
        wall_width = 2 * self.upscale_factor
        
        # 4 vertical walls
        
        v_wall_gap = self.width // 5
        for i in range(1,5):
            wall = pygame.Rect(i * v_wall_gap, self.height // 4, wall_width, self.height // 2)
            self.walls.append(wall)
        
        # 2 horizontal walls
        
        

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
                self.p1_tank.moving = True
            if event.type == BUTTON_RELEASED and event.controller == P1 and event.input in [BUTTON_B] or (event.type == pygame.KEYUP and event.key == pygame.K_UP):
                self.p1_tank.moving = False
            if event.type == BUTTON_PRESSED and event.controller == P2 and event.input in [BUTTON_B] or (event.type == pygame.KEYDOWN and event.key == pygame.K_w):
                self.p2_tank.moving = True
            if event.type == BUTTON_RELEASED and event.controller == P2 and event.input in [BUTTON_B] or (event.type == pygame.KEYUP and event.key == pygame.K_w):
                self.p2_tank.moving = False
            
            # Reset/Quit
            if self.game_over and event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()
                return
            if self.game_over and event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()
                return
                

        self.screen.fill(BLACK)

        if self.game_over:
            if self.winner == 1:
                text = self.font.render("PLAYER 1 WINS!", False, (135, 135, 0))
            else:
                text = self.font.render("PLAYER 2 WINS!", False, (135, 135, 0))
            text = pygame.transform.scale_by(text, self.upscale_factor)
            text_x = (self.width // 2) - (text.get_width() // 2)
            text_y = (self.height // 2) - (text.get_height() // 2)
            self.screen.blit(text, (text_x, text_y))
        else:

            self.p1_tank.update(dt)
            self.p2_tank.update(dt)
            
            for bullet in list(self.bullets):
                bullet.update(dt)
            
            if self.p1_tank.health <= 0:
                self.game_over = True
                self.winner = P2
            
            if self.p2_tank.health <= 0:
                self.game_over = True
                self.winner = P1
                
                
            for wall in self.walls:
                pygame.draw.rect(self.screen, WALL_COLOR, wall)
                
            # Draw the things
            for bullet in self.bullets:
                bullet.draw(self.screen)
            
            self.p1_tank.draw(self.screen)
            self.p2_tank.draw(self.screen)


