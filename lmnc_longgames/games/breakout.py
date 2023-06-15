from typing import List
import pygame
import random
import math
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
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
BALL_RADIUS = 2
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 2
TILE_ROWS = 5
TILE_COLUMNS = 4
TILE_WIDTH = 10
TILE_HEIGHT = 4
TILE_GAP = 1

PLAYER_PADDLE_MOVE_STEPS = 3

PLAYER_PADDLE_SPEED = PLAYER_PADDLE_MOVE_STEPS * 30
AI_PADDLE_SPEED = 2 * 30


class Ball:
    def __init__(self, game):
        self.game = game
        self.radius: int = BALL_RADIUS * game.upscale_factor
        self._x: int = game.width // 2
        self._y: int = game.height - (10 * game.upscale_factor)
        self.speed_x: int = 10 * random.choice([-1, 1])
        self.speed_y: int = -10

        self._rect = pygame.Rect(
            int(self._x),
            int(self._y),
            self.radius,
            self.radius,
        )

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._rect.x = int(value)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._rect.y = int(value)

    def update(self, dt):
        self.x += self.speed_x * dt * self.game.upscale_factor
        self.y += self.speed_y * dt * self.game.upscale_factor

    def draw(self):
        pygame.draw.rect(self.game.screen, WHITE, self._rect)

    def collide_paddle(self, paddle):
        if self.y + self.radius >= paddle.y and paddle.x <= self.x <= paddle.x + paddle.width:
            self.speed_y = -abs(self.speed_y)
            self.game.random_note()

    def collide_tile(self, tile):
        if self._rect.colliderect(tile._rect):
            if tile._rect.collidepoint(self._rect.topright):
                if tile._rect.collidepoint(self._rect.topleft):
                    #full top hit
                    #send down
                    self.speed_y = abs(self.speed_y)
                elif tile._rect.collidepoint(self._rect.bottomright):
                    #full right hit
                    #send left
                    self.speed_x = -abs(self.speed_x)
                else:
                    #corner hit, down and left
                    self.speed_y = abs(self.speed_y)
                    self.speed_x = -abs(self.speed_x)

            elif tile._rect.collidepoint(self._rect.topleft):
                if tile._rect.collidepoint(self._rect.bottomleft):
                    #full left hit
                    #send right
                    self.speed_x = abs(self.speed_x)
                else:
                    #corner hit, down and right
                    self.speed_y = abs(self.speed_y)
                    self.speed_x = abs(self.speed_x)
            
            elif tile._rect.collidepoint(self._rect.bottomleft):
                if tile._rect.collidepoint(self._rect.bottomright):
                    #full bottom hit
                    #send up
                    self.speed_y = -abs(self.speed_y)
                else:
                    #corner hit, up and right
                    self.speed_y = -abs(self.speed_y)
                    self.speed_x = abs(self.speed_x)
            
            elif tile._rect.collidepoint(self._rect.bottomright):
                #corner hit, up and left
                self.speed_y = -abs(self.speed_y)
                self.speed_x = -abs(self.speed_x)
            self.game.random_note(waveform=32)
            return True
        return False

    def collide_window_sides(self):
        if self.x <= 0 or self.x + self.radius >= self.game.width:
            self.speed_x *= -1
            self.game.random_note()

    def collide_window_top(self):
        if self.y <= 0:
            self.speed_y *= -1
            self.game.random_note()

    def off_screen(self):
        return self.y + self.radius >= self.game.height

class Tile:
    def __init__(self, x, y, game):
        self.game = game
        self.width = TILE_WIDTH * game.upscale_factor
        self.height = TILE_HEIGHT * game.upscale_factor
        self.x = x
        self.y = y
        self._rect = pygame.Rect(x, y, self.width, self.height)
        self.color = random.choice(PALETTE)
        self.is_visible = True

    def draw(self):
        if self.is_visible:
            pygame.draw.rect(self.game.screen, self.color, (self.x, self.y, self.width, self.height))

class Paddle:
    def __init__(self, game):
        self.game = game
        self.width = PADDLE_WIDTH * game.upscale_factor
        self.height = PADDLE_HEIGHT * game.upscale_factor
        self.x = self.game.width // 2 - self.width // 2
        self.y = self.game.height - (5 * game.upscale_factor)
        self.speed = 5

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[K_RIGHT] and self.x + self.width < self.game.width:
            self.x += self.speed

    def draw(self):
        pygame.draw.rect(self.game.screen, WHITE, (self.x, self.y, self.width, self.height))


class BreakoutGame(MultiverseGame):
    def __init__(self, multiverse_display):
        super().__init__("Breakout", 120, multiverse_display)
        self.reset()

    def reset(self):
        self.game_over = False
        self.tiles = []
        t_gap = TILE_GAP * self.upscale_factor
        t_width = TILE_WIDTH * self.upscale_factor
        t_height = TILE_HEIGHT * self.upscale_factor
        columns = len(self.multiverse_display.multiverse.displays)
        for row in range(TILE_ROWS):
            for column in range(columns):
                x = column * ((t_width) + t_gap) + t_gap
                y = row * (t_height + t_gap) + t_gap
                tile = Tile(x, y, self)
                self.tiles.append(tile)
        self.ball = Ball(self)
        self.paddle = Paddle(self)

    def loop(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independence.
        """
        # for event in events:
        #     # Player One
        #     if not self.player_one.is_ai:
        #         if event.type == pygame.KEYDOWN:
        #             if event.key == pygame.K_LEFT:
        #                 self.player_one.direction = -1
        #             elif event.key == pygame.K_RIGHT:
        #                 self.player_one.direction = 1
        #         if event.type == pygame.KEYUP:
        #             if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
        #                 self.player_one.direction = 0
        #         if event.type == ROTATED_CCW and event.controller == P1:
        #             self.player_one.move_paddle(-1 * PLAYER_PADDLE_MOVE_STEPS)
        #         if event.type == ROTATED_CW and event.controller == P1:
        #             self.player_one.move_paddle(PLAYER_PADDLE_MOVE_STEPS)
        # Update the ball and paddle
        self.ball.update(dt)
        self.paddle.update()

        # Check for collisions
        self.ball.collide_paddle(self.paddle)
        self.ball.collide_window_sides()
        self.ball.collide_window_top()

        # Check collision with tiles
        for tile in self.tiles:
            if tile.is_visible and self.ball.collide_tile(tile):
                tile.is_visible = False

        # Check if the ball is off the screen
        if self.ball.off_screen():
            self.play_note(0, 55, release=1000, waveform=32)
            self.game_over = True

        # Check if all tiles are cleared
        if all(not tile.is_visible for tile in self.tiles):
            self.game_over = True

        # Clear the window
        self.screen.fill(BLACK)


        if self.game_over:
            text, _ = self.font.render("YOU DIED", (135, 0, 0))
            if all(not tile.is_visible for tile in self.tiles):
                text, _ = self.font.render("YOU WON", (135, 135, 0))
            text = pygame.transform.scale_by(text, self.upscale_factor)
            text_x = (self.width // 2) - (text.get_width() // 2)
            text_y = (self.height // 2) - (text.get_height() // 2)
            self.screen.blit(text, (text_x, text_y))
        else:
            # Draw the ball, paddle, and tiles
            self.ball.draw()
            self.paddle.draw()
            for tile in self.tiles:
                tile.draw()


