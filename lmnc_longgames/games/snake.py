from typing import List
import pygame
import random
import math
import numpy
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.multiverse.multiverse import Multiverse
from lmnc_longgames.constants import *

UP=0
RIGHT=1
DOWN=2
LEFT=3

"""
It's snake
"""
class SnakeGame(MultiverseGame):
    def __init__(self, multiverse_display: Multiverse, game_mode=0):
        super().__init__("Snake", 120, multiverse_display)
        
        self.pixel_size = 2 * self.upscale_factor
        self.grid_width = int(self.width / self.pixel_size)
        self.grid_height = int(self.height / self.pixel_size)
        
        #These are all initialized by reset
        self.grid = None
        self.snake_head = None
        self.snake_dir = None
        self.snake_speed = None
        self.snake = None
        self.snake_target_length = None
        self.game_over = False
        
        self.reset()

    def reset(self):
        self.game_over = False
        self.grid = numpy.zeros((self.grid_width, self.grid_height))
        self.snake_head = (self.grid_width//2, self.grid_width//2)
        self.snake = [(int(self.snake_head[0]), int(self.snake_head[1]))]
        self.snake_target_length = 10
        self.snake_dir = RIGHT
        self.snake_speed = 7.0
    
    def update_snake(self, dt):
        new_x, new_y = self.snake_head
        if self.snake_dir == UP:
            new_x = new_x - (dt * self.snake_speed)
        if self.snake_dir == DOWN:
            new_x = new_x + (dt * self.snake_speed)
        if self.snake_dir == LEFT:
            new_y = new_y - (dt * self.snake_speed)
        if self.snake_dir == RIGHT:
            new_y = new_y + (dt * self.snake_speed)
        
        # TODO: Bounds check
        if new_x < 0 or new_x > self.grid_width - 1 or new_y < 0 or new_y > self.grid_height - 1:
            print("We died on a wall")
            self.game_over = True
            return
        
        #TODO: Eat apples, grow length
        
        #TODO: Increase speed
        
        int_pos = (int(new_x), int(new_y))
        if self.snake[-1] != int_pos:
            #we moved
            self.snake.append(int_pos)
            new_cell = self.grid[int_pos[0]][int_pos[1]]
            if new_cell:
                # We hit ourselves :(
                print("We hit ourselves")
                self.game_over = True
                return
            
            self.grid[int_pos[0]][int_pos[1]] = 1
            
            growing = len(self.snake) < self.snake_target_length
            if not growing:
                cleared_tail = self.snake.pop(0)
                self.grid[cleared_tail[0]][cleared_tail[1]] = 0
                
        self.snake_head = (new_x, new_y)
        
    def loop(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independence.
        """
        for event in events:
            if (event.type == ROTATED_CCW and event.controller == P1) or (event.type == pygame.KEYDOWN and event.key == pygame.K_UP):
                self.snake_dir = (self.snake_dir - 1) % 4
            if event.type == ROTATED_CW and event.controller == P1 or (event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN):
                self.snake_dir = (self.snake_dir + 1) % 4

        # Fill the screen
        self.screen.fill(BLACK)
        
        if self.game_over:
            text, _ = self.font.render("YOU DIED", (135, 0, 0))
            text = pygame.transform.scale_by(text, self.upscale_factor)
            text_x = (self.width // 2) - (text.get_width() // 2)
            text_y = (self.height // 2) - (text.get_height() // 2)
            self.screen.blit(text, (text_x, text_y))
        else:     
            # Update game elements
            self.update_snake(dt)

            self.draw_grid()

    def draw_grid(self):
        for idx, x in numpy.ndenumerate(self.grid):
            grid_x, grid_y = idx
            if x:
                pygame.draw.rect(self.screen, WHITE, pygame.Rect(grid_x * self.pixel_size, grid_y * self.pixel_size, self.pixel_size, self.pixel_size))

    def fire_controller_input_event(self, event_id: int):
        event = pygame.event.Event(event_id)
        pygame.event.post(event)
