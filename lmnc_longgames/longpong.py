from typing import List
import pygame
import random
import math
from multiverse_game import MultiverseGame

# This code is messy, it will be cleaned up at some point.....
#
# Python Dependencies: pygame, numpy, pyserial, multiverse (from https://github.com/Gadgetoid/gu-multiverse)
# 
# 3 Game Modes:
#   - One Player
#   - Two Player
#   - AI vs AI
#
# Controls:
#  - Player One: Up/Down
#  - Player Two: w/s
#  - q: Quit
#  - r: Reset Game, back to menu

# Helper Classes
class Player:
    def __init__(self, rect: pygame.Rect) -> None:
        #Paddle
        self._rect = rect
        self.direction: int = 0 # Direction the player's paddle is moving
        self.speed: int = 0
        
        #Game
        self.is_ai: bool = False
        self.score: int = 0
        self._y = rect.y
        
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        self._y = value
        self._rect.y = value
    
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
        
    def update_paddle(self, dt: float):
        speed = PLAYER_PADDLE_SPEED * game.upscale_factor
        if self.is_ai:
            update_for_ai(self)
            #Only use the slower ai speed if one player is human
            speed = AI_PADDLE_SPEED * game.upscale_factor if game.game_mode == MODE_ONE_PLAYER else speed
        self.y += speed * dt * self.direction
        self.y = max(min(self.y, game.height - PADDLE_HEIGHT), 0)

class Ball:
    def __init__(self, radius: int) -> None:
        self.radius = radius
        self.direction_y = -1
        self.direction_x = 1
        self._rect = pygame.Rect(game.width // 2 - self.radius // 2, game.height // 2 - self.radius // 2, self.radius, self.radius)
        self.reset()
        
    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        self._x = value
        self._rect.x = value
        
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        self._y = value
        self._rect.y = value
    
    def reset(self):
        self._rect.center = (game.width // 2, game.height // 2)
        self._x = self._rect.x
        self._y = self._rect.y
        self.angle = random.uniform(-math.pi / 4, math.pi / 4)
        self.speed =  ((BALL_MAX_SPEED - BALL_MIN_SPEED)/2) + BALL_MIN_SPEED
    
    @property
    def speed_x(self):
        return self.speed * math.cos(self.angle) * self.direction_x
    
    @property
    def speed_y(self):
        return self.speed * math.sin(self.angle) * self.direction_y



# Function to update the score on the screen
def draw_score():
    global font
    text = font.render(f"{player_one.score}    {player_two.score}", True, FONT_COLOR)
    text_rect = text.get_rect(center=(game.width // 2, FONT_SIZE))
    screen.blit(text, text_rect)

def update_for_ai(ai_player: Player):
    if ball.direction_x != ai_player.position or abs(ball._rect.centerx - ai_player._rect.centerx) > game.width // 2:
        ai_player.direction = 0
        return
    
    # AI Player logic
    if ai_player._rect.centery < ball._rect.centery - PADDLE_HEIGHT // 2:
        ai_player.direction = 1
    elif ai_player._rect.centery > ball._rect.centery + PADDLE_HEIGHT // 2:
        ai_player.direction = -1
    else:
        ai_player.direction = 0

def score_and_reset(player: Player):
    player.score += 1
    ball.reset()

# Function to update the ball's position
def update_ball(dt: float):
    ball.x += ball.speed_x * dt
    ball.y += ball.speed_y * dt

    # Detect Left Paddle Collision
    left_collision = ball._rect.left <= PADDLE_WIDTH and (abs(ball._rect.centery - player_one._rect.centery) <= PADDLE_HEIGHT//2)
    
    # Detect Right Paddle Collision
    right_collision = ball._rect.right >= game.width - PADDLE_WIDTH and (abs(ball._rect.centery - player_two._rect.centery) <= PADDLE_HEIGHT//2)

    # Check collision with paddles
    if left_collision:
        update_ball_speed_from_collision(player_one)

    elif right_collision:
        update_ball_speed_from_collision(player_two)

    # Check collision with walls
    if ball._rect.top <= 0 or ball._rect.bottom >= game.height:
        ball.direction_y = ball.direction_y * -1
        
    # Check if the ball went out of bounds
    if ball._rect.right <= 0:
        score_and_reset(player_two)
    elif ball._rect.left >= game.width:
        score_and_reset(player_one)

def update_ball_speed_from_collision(colliding_player: Player):
    delta_y = ball._rect.centery - colliding_player._rect.centery
    ball.angle = math.pi / 4 * (delta_y / (PADDLE_HEIGHT / 2))

    # Increase ball speed if paddle is moving in the same direction
    if colliding_player.direction * ball.speed_y > 0:
        ball.speed = min(ball.speed * 1.2, BALL_MAX_SPEED * game.upscale_factor)
    # Decrease ball speed if paddle is moving in the opposite direction
    elif colliding_player.direction * ball.speed_y < 0:
        ball.speed = max(ball.speed/1.2, BALL_MIN_SPEED * game.upscale_factor)
    # Reverse the direction of travel
    ball.direction_x = colliding_player.position * -1
    
def game_mode_callback(game_mode):    
    '''
    Called when a game mode is selected
    
    Parameters:
        game_mode: The selected game mode
    '''
    if game_mode == MODE_ONE_PLAYER:
        player_one.is_ai = False
        player_two.is_ai = True
    if game_mode == MODE_TWO_PLAYER:
        player_one.is_ai = False
        player_two.is_ai = False
    else:
        player_one.is_ai = True
        player_two.is_ai = True
    reset_game_callback()


def game_loop_callback(events: List, dt: float):
    '''
    Called for each iteration of the game loop

    Parameters:
        events: The pygame events list for this loop iteration
        dt: The delta time since the last loop iteration. This is for framerate independance.
    '''
    for event in events:
            
        # Control the player paddle
        
        #Player One
        if game.game_mode != MODE_AI_VS_AI: 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player_one.direction = -1
                elif event.key == pygame.K_DOWN:
                    player_one.direction = 1
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    player_one.direction = 0
        
        #Player Two
        if game.game_mode == MODE_TWO_PLAYER: 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    player_two.direction = -1
                elif event.key == pygame.K_s:
                    player_two.direction = 1
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    player_two.direction = 0
        
    # Update game elements
    player_one.update_paddle(dt)
    player_two.update_paddle(dt)
    update_ball(dt)

    # Fill the screen
    screen.fill(BLACK)
    
    # Draw paddles and ball
    pygame.draw.rect(screen, WHITE, player_one._rect)
    pygame.draw.rect(screen, WHITE, player_two._rect)
    pygame.draw.ellipse(screen, WHITE, ball._rect)
    
    pygame.draw.line(screen, WHITE, (game.width // 2, 0), (game.width // 2, game.height), UPSCALE_FACTOR)

    # Draw score
    draw_score()

def reset_game_callback():
    ball.reset()
    player_one.reset()
    player_two.reset()


# Setup and run the game

# Contants/Configuration
UPSCALE_FACTOR = 5

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT_SIZE = 11 * UPSCALE_FACTOR
FONT_COLOR = WHITE

BALL_RADIUS = 2 * UPSCALE_FACTOR
PADDLE_WIDTH = 2 * UPSCALE_FACTOR
PADDLE_HEIGHT = 10 * UPSCALE_FACTOR

PLAYER_PADDLE_SPEED = 3 * 30
AI_PADDLE_SPEED = 2 * 30

BALL_MAX_SPEED = 10 * 30
BALL_MIN_SPEED = 2 * 30

MODE_ONE_PLAYER = 1
MODE_TWO_PLAYER = 2
MODE_AI_VS_AI = 3

game = MultiverseGame("Long Pong", 120, UPSCALE_FACTOR, game_mode_callback, game_loop_callback, reset_game_callback)
game.configure_display()
screen = game.pygame_screen


font = pygame.font.Font("lmnc_longgames/Amble-Bold.ttf", FONT_SIZE)

# Create players
player_one = Player(pygame.Rect(0, game.height // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT))
player_two = Player(pygame.Rect(game.width - PADDLE_WIDTH, game.height // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT))

# Create ball
ball = Ball(2 * UPSCALE_FACTOR)

game.run()