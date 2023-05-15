import pygame
import random
import math
from collections import namedtuple

class Player:
    def __init__(self, rect: pygame.Rect) -> None:
        #Paddle
        self.rect = rect
        self.direction = 0
        self.speed = 0
        
        #Game
        self.ai = False
        self.score = 0

# Initialize Pygame
pygame.init()

# Set up the game window

UPSCALE_FACTOR = 1
BOARD_COUNT = 22
MATRIX_HEIGHT = 53
MATRIX_WIDTH = 11 * BOARD_COUNT

WIDTH = MATRIX_WIDTH * UPSCALE_FACTOR
HEIGHT = MATRIX_HEIGHT * UPSCALE_FACTOR
FPS = 30
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT_SIZE = 8 * UPSCALE_FACTOR
FONT_COLOR = WHITE

font = pygame.font.Font("lmnc_longpong/Amble-Bold.ttf", FONT_SIZE)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()

# Game variables
ball_radius = 2 * UPSCALE_FACTOR
paddle_width = 2 * UPSCALE_FACTOR
paddle_height = 10 * UPSCALE_FACTOR

player_paddle_speed = 2 * UPSCALE_FACTOR
ai_paddle_speed = 1 * UPSCALE_FACTOR

# Init Speed Variables
ball_speed = 1
ball_speed_x = 1
ball_speed_y = 1

ball_max_speed = 6 * UPSCALE_FACTOR
ball_min_speed = 2 * UPSCALE_FACTOR

# Create paddles
player_one = Player(pygame.Rect(0, HEIGHT // 2 - paddle_height // 2, paddle_width, paddle_height))
player_two = Player(pygame.Rect(WIDTH - paddle_width, HEIGHT // 2 - paddle_height // 2, paddle_width, paddle_height))

# Create ball
ball = pygame.Rect(WIDTH // 2 - ball_radius // 2, HEIGHT // 2 - ball_radius // 2, ball_radius, ball_radius)


# Function to update the score on the screen
def draw_score():
    global font
    text = font.render(f"P1: {player_one.score}    P2: {player_two.score}", True, FONT_COLOR)
    text_rect = text.get_rect(center=(WIDTH // 2, FONT_SIZE))
    screen.blit(text, text_rect)

# Function to update the paddles' positions
def update_paddles():
    
    #TODO Change to AI speed if needed
    player_one.rect.y += player_paddle_speed * player_one.direction
    player_two.rect.y += player_paddle_speed * player_two.direction

    # Keep the paddles inside the screen
    player_one.rect.y = max(min(player_one.rect.y, HEIGHT - paddle_height), 0)
    player_two.rect.y = max(min(player_two.rect.y, HEIGHT - paddle_height), 0)


# Function to update the ball's position
def update_ball():
    global ball_speed_x, ball_speed_y, player_one, player_two

    ball.x += ball_speed_x
    ball.y += ball_speed_y

    
    # Detect Left Paddle Collision
    left_collision = ball.left <= paddle_width and (abs(ball.centery - player_one.rect.centery) <= paddle_height//2)
    
    # Detect Right Paddle Collision
    right_collision = ball.right >= WIDTH - paddle_width and (abs(ball.centery - player_two.rect.centery) <= paddle_height//2)

    # Check collision with paddles
    if left_collision:
        delta_y = ball.centery - player_one.rect.centery
        ball_angle = math.pi / 4 * (delta_y / (paddle_height / 2))
        ball_speed = math.hypot(ball_speed_x, ball_speed_y)
        ball_speed_x = ball_speed * math.cos(ball_angle)
        ball_speed_y = ball_speed * math.sin(ball_angle)

        ball_speed_x = abs(ball_speed_x)  # Ensure the ball always moves towards the AI paddle

        # Increase ball speed if paddle is moving in the same direction
        if player_one.direction * ball_speed_y > 0:
            ball_speed_y *= 1.2
        # Decrease ball speed if paddle is moving in the opposite direction
        elif player_one.direction * ball_speed_y < 0:
            ball_speed_y /= 1.2

        ball_speed_y = max(min(ball_speed_y, ball_max_speed), -ball_max_speed)

        # Add spin to the ball based on paddle's velocity and direction
        ball_speed_x += player_one.speed * player_one.direction / 2

    elif right_collision:
        delta_y = ball.centery - player_two.rect.centery
        ball_angle = math.pi - math.pi / 4 * (delta_y / (paddle_height / 2))
        ball_speed = math.hypot(ball_speed_x, ball_speed_y)
        ball_speed_x = ball_speed * math.cos(ball_angle)
        ball_speed_y = ball_speed * math.sin(ball_angle)

        ball_speed_x = -abs(ball_speed_x)  # Ensure the ball always moves towards the player paddle

        # Increase ball speed if paddle is moving in the same direction
        if player_two.direction * ball_speed_y > 0:
            ball_speed_y *= 1.2
        # Decrease ball speed if paddle is moving in the opposite direction
        elif player_two.direction * ball_speed_y < 0:
            ball_speed_y /= 1.2

        ball_speed_y = max(min(ball_speed_y, ball_max_speed), -ball_max_speed)

        # Add spin to the ball based on paddle's velocity and direction
        ball_speed_x -= player_one.speed * player_two.direction / 2

    # Check collision with walls
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_speed_y = -ball_speed_y
        
    # Check if the ball went out of bounds
    if ball.right <= 0:
        player_two.score += 1
        reset_ball()
    elif ball.left >= WIDTH:
        player_one.score += 1
        reset_ball()

# Function to display the countdown
def display_countdown():
    global font
    for i in range(3, 0, -1):
        screen.fill(BLACK)
        countdown_text = font.render(str(i), True, WHITE)
        screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT // 2 - countdown_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.wait(1000)

# Function to reset the ball's position and speed
def reset_ball():
    global ball_speed, ball_speed_x, ball_speed_y
    
    ball.center = (WIDTH // 2, HEIGHT // 2)
    ball_angle = random.uniform(-math.pi / 4, math.pi / 4)
    ball_speed = 2 * UPSCALE_FACTOR
    ball_speed_x = ball_speed * math.cos(ball_angle)
    ball_speed_y = ball_speed * math.sin(ball_angle)


def update_for_ai(ai_paddle: Player, p2: bool):
    if p2 and ball.x < WIDTH // 2 or not p2 and ball.x > WIDTH//2:
        ai_paddle.direction = 0
        return
    
    # AI Player logic
    if ai_paddle.rect.centery < ball.centery - paddle_height // 2:
        ai_paddle.direction = 1
    elif ai_paddle.rect.centery > ball.centery + paddle_height // 2:
        ai_paddle.direction = -1
    else:
        ai_paddle.direction = 0
    
# Game loop
running = True

display_countdown()
reset_ball()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Control the player paddle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                player_one.direction = -1
            elif event.key == pygame.K_DOWN:
                player_one.direction = 1
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                player_one.direction = 0

    update_for_ai(player_two, True)

    # Update game elements
    update_paddles()
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

    # Update the display
    pygame.display.flip()

    # Set the frame rate
    clock.tick(FPS)

# Quit the game
pygame.quit()

