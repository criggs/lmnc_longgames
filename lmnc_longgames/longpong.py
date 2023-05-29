import sys, os
import getopt
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
    def __init__(self, rect: pygame.Rect, game) -> None:
        #Paddle
        self._rect = rect
        self.direction: int = 0 # Direction the player's paddle is moving
        self.speed: int = 0
        
        #Game
        self.is_ai: bool = False
        self.score: int = 0
        self._y = rect.y
        self.game = game
        
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
        if self.is_ai:
            self.game.update_for_ai(self)
            #Only use the slower ai speed if one player is human
            speed = AI_PADDLE_SPEED * self.game.upscale_factor if self.game.game_mode == MODE_ONE_PLAYER else speed
        self.y += speed * dt * self.direction
        self.y = max(min(self.y, self.game.height - self.height), 0)

class Ball:
    def __init__(self, radius: int, game: MultiverseGame) -> None:
        self.radius = radius
        self.direction_y = -1
        self.direction_x = 1
        self.game = game
        self._rect = pygame.Rect(self.game.width // 2 - self.radius // 2, self.game.height // 2 - self.radius // 2, self.radius, self.radius)
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
        self.angle = random.uniform(-math.pi / 4, math.pi / 4)
        self.speed =  ((BALL_MAX_SPEED - BALL_MIN_SPEED)/2) + BALL_MIN_SPEED
    
    @property
    def speed_x(self):
        return self.speed * math.cos(self.angle) * self.direction_x
    
    @property
    def speed_y(self):
        return self.speed * math.sin(self.angle) * self.direction_y

class LongPongGame(MultiverseGame):
    def __init__(self, upscale_factor):
        super().__init__("Long Pong", 120, upscale_factor)
        self.configure_display()
        self.screen = self.pygame_screen

        script_path = os.path.realpath(os.path.dirname(__file__))
        self.font = pygame.font.Font(f"{script_path}/Amble-Bold.ttf", FONT_SIZE)



        paddle_width = 2 * self.upscale_factor
        paddle_height = 10 * self.upscale_factor

        # Create players
        self.player_one = Player(pygame.Rect(0, self.height // 2 - paddle_height // 2, paddle_width, paddle_height), self)
        self.player_two = Player(pygame.Rect(self.width - paddle_width, self.height // 2 - paddle_height // 2, paddle_width, paddle_height), self)

        # Create ball
        ball_radius = 2 * self.upscale_factor
        self.ball = Ball(ball_radius, self)

    # Function to update the score on the screen
    def draw_score(self):
        text = self.font.render(f"{self.player_one.score}    {self.player_two.score}", True, FONT_COLOR)
        text_rect = text.get_rect(center=(self.width // 2, FONT_SIZE))
        self.screen.blit(text, text_rect)

    def update_for_ai(self, ai_player: Player):
        if self.ball.direction_x != ai_player.position or abs(self.ball._rect.centerx - ai_player._rect.centerx) > self.width // 2:
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
        print(f'Score: {self.player_one.score}/{self.player_two.score}')
        self.ball.reset()

    # Function to update the ball's position
    def update_ball(self, dt: float):
        self.ball.x += self.ball.speed_x * dt
        self.ball.y += self.ball.speed_y * dt

        # Detect Left Paddle Collision
        left_collision = self.ball._rect.left <= self.player_one.width and (abs(self.ball._rect.centery - self.player_one._rect.centery) <= self.player_one.height//2)
        
        # Detect Right Paddle Collision
        right_collision = self.ball._rect.right >= self.width - self.player_two.width and (abs(self.ball._rect.centery - self.player_two._rect.centery) <= self.player_two.height//2)

        # Check collision with paddles
        if left_collision:
            self.update_ball_speed_from_collision(self.player_one)

        elif right_collision:
            self.update_ball_speed_from_collision(self.player_two)

        # Check collision with walls
        if self.ball._rect.top <= 0 or self.ball._rect.bottom >= self.height:
            self.ball.direction_y = self.ball.direction_y * -1
            
        # Check if the ball went out of bounds
        if self.ball._rect.right <= 0:
            self.score_and_reset(self.player_two)
        elif self.ball._rect.left >= self.width:
            self.score_and_reset(self.player_one)

    def update_ball_speed_from_collision(self, colliding_player: Player):
        delta_y = self.ball._rect.centery - colliding_player._rect.centery
        self.ball.angle = math.pi / 4 * (delta_y / (colliding_player.height / 2))

        # Increase ball speed if paddle is moving in the same direction
        if colliding_player.direction * self.ball.speed_y > 0:
            self.ball.speed = min(self.ball.speed * 1.2, BALL_MAX_SPEED * self.upscale_factor)
        # Decrease ball speed if paddle is moving in the opposite direction
        elif colliding_player.direction * self.ball.speed_y < 0:
            self.ball.speed = max(self.ball.speed/1.2, BALL_MIN_SPEED * self.upscale_factor)
        # Reverse the direction of travel
        self.ball.direction_x = colliding_player.position * -1
        
    def game_mode_callback(self, game_mode):    
        """
        Called when a game mode is selected
        
        Parameters:
            game_mode: The selected game mode
        """
        print(f'Playing game mode {game_mode}')
        self.reset_game_callback()
        if self.game_mode == MODE_ONE_PLAYER:
            self.player_one.is_ai = False
            self.player_two.is_ai = True
        elif self.game_mode == MODE_TWO_PLAYER:
            self.player_one.is_ai = False
            self.player_two.is_ai = False
        else:
            self.player_one.is_ai = True
            self.player_two.is_ai = True



    def game_loop_callback(self, events: List, dt: float):
        """
        Called for each iteration of the game loop

        Parameters:
            events: The pygame events list for this loop iteration
            dt: The delta time since the last loop iteration. This is for framerate independance.
        """
        for event in events:
            
            #TODO: Make the controls work with GPIO/Joysticks    
            # Control the player paddle
            
            #Player One
            if self.game_mode != MODE_AI_VS_AI: 
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.player_one.direction = -1
                    elif event.key == pygame.K_DOWN:
                        self.player_one.direction = 1
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        self.player_one.direction = 0
            
            #Player Two
            if self.game_mode == MODE_TWO_PLAYER: 
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.player_two.direction = -1
                    elif event.key == pygame.K_s:
                        self.player_two.direction = 1
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_w or event.key == pygame.K_s:
                        self.player_two.direction = 0
            
        # Update game elements
        self.player_one.update_paddle(dt)
        self.player_two.update_paddle(dt)
        self.update_ball(dt)

        # Fill the screen
        self.screen.fill(BLACK)
        
        # Draw paddles and ball
        pygame.draw.rect(self.screen, WHITE, self.player_one._rect)
        pygame.draw.rect(self.screen, WHITE, self.player_two._rect)
        pygame.draw.ellipse(self.screen, WHITE, self.ball._rect)
        
        pygame.draw.line(self.screen, WHITE, (self.width // 2, 0), (self.width // 2, self.height), UPSCALE_FACTOR)

        # Draw score
        self.draw_score()

    def reset_game_callback(self):
        self.ball.reset()
        self.player_one.reset()
        self.player_two.reset()


# Setup and run the game

# Contants/Configuration
UPSCALE_FACTOR = 5

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT_SIZE = 11 * UPSCALE_FACTOR
FONT_COLOR = WHITE


PLAYER_PADDLE_SPEED = 3 * 30
AI_PADDLE_SPEED = 2 * 30

BALL_MAX_SPEED = 10 * 30
BALL_MIN_SPEED = 2 * 30

MODE_ONE_PLAYER = 1
MODE_TWO_PLAYER = 2
MODE_AI_VS_AI = 3

    # Generate a list of IDs for the config in the correct order

def main():
    # Script Args
    config_file = ''
    show_window = False
    debug = False
    opts, args = getopt.getopt(sys.argv[1:],"hi:wd",["conf="])
    for opt, arg in opts:
        if opt == '-h':
            print ('longpong.py [-w] [-d] -c CONFIG_FILE')
            sys.exit()
        elif opt in ('-c', '--conf'):
            #TODO: Get the display configuration and GPIO/Input info from a config file
            config_file = arg
        elif opt == '-w':
            show_window = True
        elif opt == '-d':
            debug = True

    if not show_window:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    longpong = LongPongGame(UPSCALE_FACTOR)
    longpong.run()


if __name__ == "__main__":
    main()


