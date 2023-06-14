from typing import List
import pygame
import random
import math
import numpy
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.multiverse import Multiverse
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
        
        self.reset()

    def reset(self):
        self.game_over = False
        self.grid = numpy.zeros((self.grid_width, self.grid_height))
        self.snake_head = (self.grid_width//2, self.grid_height//2)
        self.snake = [(int(self.snake_head[0]), int(self.snake_head[1]))]
        self.snake_target_length = 10
        self.snake_dir = random.choice([UP,DOWN,LEFT,RIGHT])
        self.snake_speed = 5.0
        self.food_timer = 3.0
        self.food_position = None
        self.speedup_timer = 5.0
    
    def update_snake(self, dt):
        
        # Speed up a bit
        self.speedup_timer = self.speedup_timer - dt
        if self.speedup_timer <= 0:
            self.speedup_timer = 5.0
            self.snake_speed = self.snake_speed + 0.1
            print(f'Speed is now {self.snake_speed}')
        
        new_x, new_y = self.snake_head
        if self.snake_dir == UP:
            new_x = new_x - (dt * self.snake_speed)
        if self.snake_dir == DOWN:
            new_x = new_x + (dt * self.snake_speed)
        if self.snake_dir == LEFT:
            new_y = new_y - (dt * self.snake_speed)
        if self.snake_dir == RIGHT:
            new_y = new_y + (dt * self.snake_speed)
        
        # Bounds check
        if new_x < 0 or new_x > self.grid_width or new_y < 0 or new_y > self.grid_height:
            print(f"We died on a wall 0,0,{self.grid_width},{self.grid_height}. {new_x},{new_y} ")
            self.game_over = True
            return
        
        
        int_pos = (int(new_x), int(new_y))
        if self.snake[-1] != int_pos:
            #we moved
            self.snake.append(int_pos)
            new_cell = self.grid[int_pos[0]][int_pos[1]]
            if new_cell == 1:
                # We hit ourselves :(
                print("We hit ourselves")
                self.game_over = True
                return
            if new_cell == 2:
                # We got food!
                self.food_position = None
                self.snake_target_length = self.snake_target_length + 5
                print("Ate an apple. Yum :)")
            
            self.grid[int_pos[0]][int_pos[1]] = 1
            
            growing = len(self.snake) < self.snake_target_length
            if not growing:
                cleared_tail = self.snake.pop(0)
                self.grid[cleared_tail[0]][cleared_tail[1]] = 0
                
        self.snake_head = (new_x, new_y)
        
    def update_food(self, dt):
        
        self.food_timer = self.food_timer - dt
        if self.food_timer <= 0:
            self.food_timer = 10.0
            
            # Remove old food
            if self.food_position is not None:
                self.grid[self.food_position[0]][self.food_position[1]] = 0
                
            # New food
            self.food_position = random.choice(numpy.argwhere(self.grid==0))
            self.grid[self.food_position[0]][self.food_position[1]] = 2
        
        
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
            if self.game_over and event.type == BUTTON_RELEASED and event.controller == P1 and event.input in [BUTTON_A, BUTTON_B, ROTARY_PUSH]:
                self.reset()
                return

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
            self.update_food(dt)
            self.draw_grid()

    def draw_grid(self):
        for idx, x in numpy.ndenumerate(self.grid):
            grid_x, grid_y = idx
            if x == 1:
                color = (50, 100, 0)
                if idx == self.snake[0]:
                    #tail
                    color = (100, 100, 0)
                if idx == self.snake[-1]:
                    #head
                    color = (0, 200, 0)
                    
                pygame.draw.rect(self.screen, color, pygame.Rect(grid_x * self.pixel_size, grid_y * self.pixel_size, self.pixel_size, self.pixel_size))
            if x == 2:
                pygame.draw.rect(self.screen, (135,0,0), pygame.Rect(grid_x * self.pixel_size, grid_y * self.pixel_size, self.pixel_size, self.pixel_size))
                pygame.draw.rect(self.screen, (0,135,0), pygame.Rect(grid_x * self.pixel_size + self.pixel_size - self.upscale_factor, grid_y * self.pixel_size, self.upscale_factor, self.upscale_factor))

    def fire_controller_input_event(self, event_id: int):
        event = pygame.event.Event(event_id)
        pygame.event.post(event)
