import time
from typing import List
import pygame
import random
import math
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.constants import *
from lmnc_longgames.sound.microphone import Microphone
import logging

MODE_AI_VS_AI = 0
MODE_ONE_PLAYER = 1
MODE_TWO_PLAYER = 2

PLAYER_PADDLE_MOVE_STEPS = 3

PLAYER_PADDLE_SPEED = PLAYER_PADDLE_MOVE_STEPS * 30
AI_PADDLE_SPEED = 2 * 30

POINTS_TO_WIN = 5

CODE_1 = [
    (ROTATED_CCW, ROTARY_PUSH),
    (ROTATED_CW, ROTARY_PUSH),
    (ROTATED_CCW, ROTARY_PUSH),
    (ROTATED_CW, ROTARY_PUSH),
    (BUTTON_RELEASED, BUTTON_B),
    (BUTTON_RELEASED, BUTTON_A),
    (BUTTON_RELEASED, ROTARY_PUSH)
]

"""
longpong
"""


class Player:
    def __init__(self, rect: pygame.Rect, game, player_id, is_ai: bool) -> None:
        # Paddle
        self._rect = rect
        self.direction: int = 0  # Direction the player's paddle is moving
        self.speed: int = 0
        self.player_id = player_id

        # Game
        self.is_ai = is_ai
        self.score: int = 0
        self._y = rect.y
        self.game = game
        self.microphone = None
        if not is_ai and self.game.audio_pong:
            device_name = self.game.config.config.get("audio", {}).get(f"p{player_id}")
            self.microphone = Microphone(device_name)

    def teardown(self):
        if self.microphone is not None:
            self.microphone.teardown()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._rect.y = int(value)

    # Side of the board the player is on
    @property
    def position(self):
        if self._rect.x == 0:
            return -1
        return 1

    def reset(self):
        self.y = 0
        self.speed = 0
        self.score = 0
        self.direction = 0

    @property
    def width(self):
        return self._rect.w

    @property
    def height(self):
        return self._rect.h

    def update_paddle(self, dt: float):
        speed = PLAYER_PADDLE_SPEED * self.game.upscale_factor
        if self.microphone is not None:
            buffer = self.microphone.read_audio_buffer(1)
            if buffer is None:
                logging.info(f"No audio buffer from microphone for player {self.player_id}")
                return
            # get the max value of the buffer
            max_value = max(max(buffer), abs( min(buffer)))
            position_factor = (max_value / 32768) 

            if position_factor > 0.5:
                self.direction = 1
            else:
                self.direction = -1
            
        else:
            if self.is_ai:
                self.game.update_for_ai(self)
                # Only use the slower ai speed if one player is human
                speed = (
                    speed
                    if self.game.player_one.is_ai
                    else AI_PADDLE_SPEED * self.game.upscale_factor
                )

        self.y += speed * dt * self.direction
        self.y = max(min(self.y, self.game.height - self.height), 0)

    def move_paddle(self, steps: float):
        self.y += steps * self.game.upscale_factor
        self.y = max(min(self.y, self.game.height - self.height), 0)


class Ball:
    max_speed = 80
    min_speed = 15

    def __init__(self, radius: int, game: MultiverseGame) -> None:
        self.radius = radius
        self.direction_y = -1
        self.direction_x = 1
        self.game = game
        self._rect = pygame.Rect(
            self.game.width // 2 - self.radius // 2,
            self.game.height // 2 - self.radius // 2,
            self.radius,
            self.radius,
        )
        self.reset()

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

    def reset(self):
        self._rect.center = (self.game.width // 2, self.game.height // 2)
        self._x = self._rect.x
        self._y = self._rect.y
        self.angle = random.uniform(0.2, math.pi / 4)
        self.direction_y = random.choice((-1, 1))
        self.speed = ((self.max_speed - self.min_speed) / 2) + self.min_speed
        self.speed_multiplier = 1.0

    def speedup(self):
        self.speed_multiplier = self.speed_multiplier + 0.075

    @property
    def speed_x(self):
        return self.speed * math.cos(self.angle) * self.direction_x * self.speed_multiplier

    @property
    def speed_y(self):
        return self.speed * math.sin(self.angle) * self.direction_y * self.speed_multiplier


class LongPongGame(MultiverseGame):
    def __init__(self, multiverse_display, game_mode=0, audio_pong=False):
        super().__init__("Long Pong", 120, multiverse_display)
        print(f"Game Mode: {game_mode}")

        paddle_width = 2 * self.upscale_factor
        paddle_height = 10 * self.upscale_factor
        self.audio_pong = audio_pong

        # Create players
        self.player_one = Player(
            pygame.Rect(
                0, self.height // 2 - paddle_height // 2, paddle_width, paddle_height
            ),
            self,
            P1,
            game_mode == MODE_AI_VS_AI
        )

        print(f"Player One is AI? {self.player_one.is_ai}")

        self.player_two = Player(
            pygame.Rect(
                self.width - paddle_width,
                self.height // 2 - paddle_height // 2,
                paddle_width,
                paddle_height,
            ),
            self,
            P2,
            game_mode != MODE_TWO_PLAYER
        )
        
        print(f"Player Two is AI? {self.player_two.is_ai}")

        # Create ball
        ball_radius = 2 * self.upscale_factor
        self.ball = Ball(ball_radius, self)

    # Function to update the score on the screen
    def draw_score(self):
        text = self.font.render(
            f"{self.player_one.score}    {self.player_two.score}", False,  WHITE
        )
        text = pygame.transform.scale_by(text, self.upscale_factor)
        text_rect = text.get_rect(center=(self.width // 2, 10 * self.upscale_factor))
        self.screen.blit(text, text_rect)

    def update_for_ai(self, ai_player: Player):
        if (
            self.ball.direction_x != ai_player.position
            or abs(self.ball._rect.centerx - ai_player._rect.centerx) > self.width // 2
        ):
            ai_player.direction = 0
            return

        # AI Player logic
        if ai_player._rect.centery < self.ball._rect.centery - ai_player.height // 2:
            ai_player.direction = 1
        elif ai_player._rect.centery > self.ball._rect.centery + ai_player.height // 2:
            ai_player.direction = -1
        else:
            ai_player.direction = 0

    def score_and_reset(self, player: Player):
        player.score += 1
        print(f"Score: {self.player_one.score}/{self.player_two.score}")
        self.ball.reset()
        self.play_note(0, 55, release=1000, waveform=32)

        if player.score == POINTS_TO_WIN:
            self.win_note()
            self.game_over = True
            self.winner = player.player_id

    # Function to update the ball's position
    def update_ball(self, dt: float):
        self.ball.x += self.ball.speed_x * dt * self.upscale_factor
        self.ball.y += self.ball.speed_y * dt * self.upscale_factor

        # Detect Left Paddle Collision
        left_collision = self.ball._rect.left <= self.player_one.width and (
            abs(self.ball._rect.centery - self.player_one._rect.centery)
            <= self.player_one.height // 2
        )

        # Detect Right Paddle Collision
        right_collision = (
            self.ball._rect.right >= self.width - self.player_two.width
            and (
                abs(self.ball._rect.centery - self.player_two._rect.centery)
                <= self.player_two.height // 2
            )
        )

        # Check collision with paddles
        if left_collision:
            self.update_ball_from_collision(self.player_one)

        elif right_collision:
            self.update_ball_from_collision(self.player_two)

        # Check collision with top
        if self.ball._rect.top <= 0:
            self.ball.direction_y = 1
            #self.random_note()
            self.play_song_note()

        # Check collision with bottom
        if self.ball._rect.bottom >= (self.height - 1):
            self.ball.direction_y = -1
            #self.random_note()
            self.play_song_note()

        # Check if the ball went out of bounds
        if self.ball._rect.right <= 0:
            self.score_and_reset(self.player_two)
        elif self.ball._rect.left >= self.width:
            self.score_and_reset(self.player_one)

    def update_ball_from_collision(self, colliding_paddle: Player):
        delta_y = abs(self.ball._rect.centery - colliding_paddle._rect.centery)
        self.ball.angle = math.pi / 4 * (delta_y / (colliding_paddle.height / 2))

        # keep ball from getting stuck in a stalemate
        if self.ball.angle < 0.01:
            self.ball.angle = 0.02

        # Increase ball speed if paddle is moving in the same direction
        if colliding_paddle.direction * self.ball.speed_y > 0:
            self.ball.speed = min(self.ball.speed * 1.2, self.ball.max_speed)
        # Decrease ball speed if paddle is moving in the opposite direction
        elif colliding_paddle.direction * self.ball.speed_y < 0:
            self.ball.speed = max(self.ball.speed / 1.2, self.ball.min_speed)
        # Reverse the direction of travel
        self.ball.direction_x = colliding_paddle.position * -1

        self.ball.speedup()

        # Beep!
        #self.random_note()
        self.play_song_note()
        
    def loop(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independence.
        """
        super().loop(events, dt)

        if self.has_history(P1, CODE_1):
            self.reset_input_history(P1)
            self.player_one._rect.height = 10 * self.upscale_factor * 2
            print("Code 1 for P1")
        if self.has_history(P2, CODE_1):
            self.reset_input_history(P2)
            self.player_two._rect.height = 10 * self.upscale_factor * 2
            print("Code 1 for P2")

        for event in events:
            # Player One
            if not self.player_one.is_ai:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.player_one.direction = -1
                    elif event.key == pygame.K_DOWN:
                        self.player_one.direction = 1
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        self.player_one.direction = 0
                if event.type == ROTATED_CCW and event.controller == P1:
                    self.player_one.move_paddle(-1 * PLAYER_PADDLE_MOVE_STEPS)
                if event.type == ROTATED_CW and event.controller == P1:
                    self.player_one.move_paddle(PLAYER_PADDLE_MOVE_STEPS)

            # Player Two
            if not self.player_two.is_ai:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.player_two.direction = -1
                    elif event.key == pygame.K_s:
                        self.player_two.direction = 1
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_w or event.key == pygame.K_s:
                        self.player_two.direction = 0
                if event.type == ROTATED_CCW and event.controller == P2:
                    self.player_two.move_paddle(-1 * PLAYER_PADDLE_MOVE_STEPS)
                if event.type == ROTATED_CW and event.controller == P2:
                    self.player_two.move_paddle(PLAYER_PADDLE_MOVE_STEPS)

        if self.game_over:
            self.game_over_loop(events)

            if self.player_one.is_ai and self.player_two.is_ai:
                # Automatically reset the game if both players are AI
                if time.time() - self.game_over_start_time > 5:
                    self.reset()
                    return

        else:
            self.screen.fill(BLACK)
            # Update game elements
            self.player_one.update_paddle(dt)
            self.player_two.update_paddle(dt)
            self.update_ball(dt)

            # Draw paddles and ball
            pygame.draw.rect(self.screen, WHITE, self.player_one._rect)
            pygame.draw.rect(self.screen, WHITE, self.player_two._rect)
            pygame.draw.rect(self.screen, WHITE, self.ball._rect)

            pygame.draw.line(
                self.screen,
                WHITE,
                (self.width // 2, 0),
                (self.width // 2, self.height),
                self.upscale_factor,
            )
            # Draw score
            self.draw_score()

    def reset(self):
        super().reset()
        self.ball.reset()
        self.player_one.reset()
        self.player_two.reset()
    
    def teardown(self):
        super().teardown()
        self.player_one.teardown()
        self.player_two.teardown()

