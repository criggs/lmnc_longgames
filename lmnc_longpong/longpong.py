import time
import pygame
import random
import math
import numpy
from multiverse import Multiverse, Display

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


# TODO: Configure display
# display = Multiverse(
#     #       Serial Port,            W,  H,  X,  Y
#    Display("/dev/serial/by-id/_01", 53, 11, 0, 0),
#    Display("/dev/serial/by-id/_02", 53, 11, 0, 11),
#    Display("/dev/serial/by-id/_03", 53, 11, 0, 22),
#    Display("/dev/serial/by-id/_04", 53, 11, 0, 33),
#    Display("/dev/serial/by-id/_05", 53, 11, 0, 44),
#    Display("/dev/serial/by-id/_06", 53, 11, 0, 55),
#    Display("/dev/serial/by-id/_07", 53, 11, 0, 66),
#    Display("/dev/serial/by-id/_08", 53, 11, 0, 77),
#    Display("/dev/serial/by-id/_09", 53, 11, 0, 88),
#    Display("/dev/serial/by-id/_10", 53, 11, 0, 99),
#    Display("/dev/serial/by-id/_11", 53, 11, 0, 110),
#    Display("/dev/serial/by-id/_12", 53, 11, 0, 121,
#    Display("/dev/serial/by-id/_13", 53, 11, 0, 132),
#    Display("/dev/serial/by-id/_14", 53, 11, 0, 143),
#    Display("/dev/serial/by-id/_15", 53, 11, 0, 154),
#    Display("/dev/serial/by-id/_16", 53, 11, 0, 165),
#    Display("/dev/serial/by-id/_17", 53, 11, 0, 176),
#    Display("/dev/serial/by-id/_18", 53, 11, 0, 187),
#    Display("/dev/serial/by-id/_19", 53, 11, 0, 198),
#    Display("/dev/serial/by-id/_20", 53, 11, 0, 209),
#    Display("/dev/serial/by-id/_21", 53, 11, 0, 220),
# )
# display.setup()

# Contants/Configuration
UPSCALE_FACTOR = 6

BOARD_COUNT = 10 # len(display.displays)
MATRIX_HEIGHT = 53
MATRIX_WIDTH = 22 * BOARD_COUNT

WIDTH = MATRIX_WIDTH * UPSCALE_FACTOR
HEIGHT = MATRIX_HEIGHT * UPSCALE_FACTOR
FPS = 120
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT_SIZE = 11 * UPSCALE_FACTOR
FONT_COLOR = WHITE

BALL_RADIUS = 2 * UPSCALE_FACTOR
PADDLE_WIDTH = 2 * UPSCALE_FACTOR
PADDLE_HEIGHT = 10 * UPSCALE_FACTOR

PLAYER_PADDLE_SPEED = 3 * 30 * UPSCALE_FACTOR
AI_PADDLE_SPEED = 2 * 30 * UPSCALE_FACTOR

BALL_MAX_SPEED = 20 * 30 * UPSCALE_FACTOR
BALL_MIN_SPEED = 4 * 30 * UPSCALE_FACTOR

MODE_ONE_PLAYER = 1
MODE_TWO_PLAYER = 2
MODE_AI_VS_AI = 3

# Game State/Settings
gameMode = 1
menuSelection = True
running = True

# Helper Classes
class Player:
    def __init__(self, rect: pygame.Rect) -> None:
        #Paddle
        self.rect = rect
        self.direction: int = 0 # Direction the player's paddle is moving
        self.speed: int = 0
        
        #Game
        self.is_ai: bool = False
        self.score: int = 0
    
    # Side of the board the player is on
    @property
    def position(self):
        if self.rect.x == 0:
            return -1
        return 1
        
    def reset(self):
        self.rect.y = 0
        self.speed = 0
        self.score = 0
        self.direction = 0
        
    def update_paddle(self):
        global gameMode, dt
        speed = PLAYER_PADDLE_SPEED
        if self.is_ai:
            update_for_ai(self)
            #Only use the slower ai speed if one player is human
            speed = AI_PADDLE_SPEED if gameMode == MODE_ONE_PLAYER else PLAYER_PADDLE_SPEED
        self.rect.y += speed * dt * self.direction
        self.rect.y = max(min(self.rect.y, HEIGHT - PADDLE_HEIGHT), 0)

class Ball:
    def __init__(self, radius: int) -> None:
        self.radius = radius
        self.direction_y = -1
        self.direction_x = 1
        self.speed = 30 * UPSCALE_FACTOR
        self.angle = 0
        self.rect = pygame.Rect(WIDTH // 2 - self.radius // 2, HEIGHT // 2 - self.radius // 2, self.radius, self.radius)
        
    def reset(self):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.angle = random.uniform(-math.pi / 4, math.pi / 4)
        self.speed = random.uniform(40 * UPSCALE_FACTOR, 80 * UPSCALE_FACTOR)
    
    @property
    def speed_x(self):
        return self.speed * math.cos(self.angle) * self.direction_x
    
    @property
    def speed_y(self):
        return self.speed * math.sin(self.angle) * self.direction_y

# Initialize Pygame
pygame.init()

# Set up the game window

def flip_display():
    pygame.display.flip()
    # TODO: Grab the frame buffer, downsample with a numpy slice, pass to the multiverse. Do we need to convert?
    framegrab = pygame.surfarray.array2d(screen)
    downsample = numpy.array(framegrab)[::UPSCALE_FACTOR,::UPSCALE_FACTOR]
    # Update the displays from the buffer
    #display.update(downsample)


screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Pong")

clock = pygame.time.Clock()

font = pygame.font.Font(None, FONT_SIZE)

# Create players
player_one = Player(pygame.Rect(0, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT))
player_two = Player(pygame.Rect(WIDTH - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT))

# Create ball
ball = Ball(2 * UPSCALE_FACTOR)

# Function to update the score on the screen
def draw_score():
    global font
    text = font.render(f"{player_one.score}    {player_two.score}", True, FONT_COLOR)
    text_rect = text.get_rect(center=(WIDTH // 2, FONT_SIZE))
    screen.blit(text, text_rect)

def update_for_ai(ai_player: Player):
    if ball.direction_x != ai_player.position or abs(ball.rect.centerx - ai_player.rect.centerx) > WIDTH // 2:
        ai_player.direction = 0
        return
    
    # AI Player logic
    if ai_player.rect.centery < ball.rect.centery - PADDLE_HEIGHT // 2:
        ai_player.direction = 1
    elif ai_player.rect.centery > ball.rect.centery + PADDLE_HEIGHT // 2:
        ai_player.direction = -1
    else:
        ai_player.direction = 0

def score_and_reset(player: Player):
    player.score += 1
    ball.reset()

# Function to update the ball's position
def update_ball():
    ball.rect.x += ball.speed_x * dt
    ball.rect.y += ball.speed_y * dt

    # Detect Left Paddle Collision
    left_collision = ball.rect.left <= PADDLE_WIDTH and (abs(ball.rect.centery - player_one.rect.centery) <= PADDLE_HEIGHT//2)
    
    # Detect Right Paddle Collision
    right_collision = ball.rect.right >= WIDTH - PADDLE_WIDTH and (abs(ball.rect.centery - player_two.rect.centery) <= PADDLE_HEIGHT//2)

    # Check collision with paddles
    if left_collision:
        update_ball_speed_from_collision(player_one)

    elif right_collision:
        update_ball_speed_from_collision(player_two)

    # Check collision with walls
    if ball.rect.top <= 0 or ball.rect.bottom >= HEIGHT:
        ball.direction_y = ball.direction_y * -1
        
    # Check if the ball went out of bounds
    if ball.rect.right <= 0:
        score_and_reset(player_two)
    elif ball.rect.left >= WIDTH:
        score_and_reset(player_one)

def update_ball_speed_from_collision(colliding_player: Player):
    delta_y = ball.rect.centery - colliding_player.rect.centery
    ball.angle = math.pi / 4 * (delta_y / (PADDLE_HEIGHT / 2))

    # Increase ball speed if paddle is moving in the same direction
    if colliding_player.direction * ball.speed_y > 0:
        ball.speed = min(ball.speed * 1.2, BALL_MAX_SPEED)
    # Decrease ball speed if paddle is moving in the opposite direction
    elif colliding_player.direction * ball.speed_y < 0:
        ball.speed = min (ball.speed/1.2, BALL_MIN_SPEED)
    # Reverse the direction of travel
    ball.direction_x = colliding_player.position * -1
    
# Function to display the countdown
def display_countdown():
    for i in range(3, 0, -1):
        screen.fill(BLACK)
        countdown_text = font.render(str(i), True, WHITE)
        screen.blit(countdown_text, (WIDTH // 4 - countdown_text.get_width() // 2, HEIGHT // 2 - countdown_text.get_height() // 2))
        screen.blit(countdown_text, (3 * WIDTH // 4 - countdown_text.get_width() // 2, HEIGHT // 2 - countdown_text.get_height() // 2))
        flip_display()
        pygame.time.wait(1000)

def reset_game():
    global menuSelection, gameMode
    screen.fill(BLACK)

    ball.reset()
    player_one.reset()
    player_two.reset()
        
    menuSelection = True


def menuLoop():
    global running, gameMode, menuSelection, dt, prev_time
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Control the player paddle
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_q:
                running = False
            if event.key == pygame.K_1:
                gameMode = 1
                menuSelection = False
            if event.key == pygame.K_2:
                gameMode = 2
                menuSelection = False
            if event.key == pygame.K_3:
                gameMode = 3
                menuSelection = False
                
    # Fill the screen
    screen.fill(BLACK)

    title_text = font.render("Select Game Mode", True, WHITE)
    mode1_text = font.render("1. 1 Player", True, WHITE)
    mode2_text = font.render("2. 2 Players", True, WHITE)
    mode3_text = font.render("3. AI vs AI", True, WHITE)
    
    
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 5 * UPSCALE_FACTOR))
    screen.blit(mode1_text, (WIDTH // 2 - mode1_text.get_width() // 2, 15 * UPSCALE_FACTOR))
    screen.blit(mode2_text, (WIDTH // 2 - mode2_text.get_width() // 2, 25 * UPSCALE_FACTOR))
    screen.blit(mode3_text, (WIDTH // 2 - mode3_text.get_width() // 2, 35 * UPSCALE_FACTOR))
    
    # The user selected an option
    if not menuSelection:
        if gameMode == MODE_ONE_PLAYER:
            player_one.is_ai = False
            player_two.is_ai = True
        elif gameMode == MODE_TWO_PLAYER:
            player_one.is_ai = False
            player_two.is_ai = False
        else:
            player_one.is_ai = True
            player_two.is_ai = True
        
        display_countdown()
        player_one.reset()
        player_two.reset()
        ball.reset()
        dt = 0
        prev_time = time.time()


def gameLoop():
    global running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Control the player paddle
        
        #Player One
        if gameMode != MODE_AI_VS_AI: 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player_one.direction = -1
                elif event.key == pygame.K_DOWN:
                    player_one.direction = 1
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    player_one.direction = 0
        
        #Player Two
        if gameMode == MODE_TWO_PLAYER: 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    player_two.direction = -1
                elif event.key == pygame.K_s:
                    player_two.direction = 1
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    player_two.direction = 0
        
        # Game Lifecycle Controls
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_r:
                reset_game()
            if event.key == pygame.K_q:
                running = False

    # Update game elements
    player_one.update_paddle()
    player_two.update_paddle()
    update_ball()

    # Fill the screen
    screen.fill(BLACK)
    
    # Draw paddles and ball
    pygame.draw.rect(screen, WHITE, player_one)
    pygame.draw.rect(screen, WHITE, player_two)
    pygame.draw.ellipse(screen, WHITE, ball)
    
    pygame.draw.line(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), UPSCALE_FACTOR)

    # Draw score
    draw_score()

# Game loop

reset_game()


prev_time = time.time()
dt = 0

while running:
    
    now = time.time()
    dt = now - prev_time
    prev_time = now
    
    if menuSelection:
        menuLoop()
    else:
        gameLoop()
    # Update the display
    flip_display()
        
    # Set the frame rate
    clock.tick(FPS)

# Quit the game
pygame.quit()
