import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Set up the game window
WIDTH = 800
HEIGHT = 400
FPS = 60
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT_SIZE = 32
FONT_COLOR = WHITE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()

# Game variables
ball_radius = 10
paddle_width = 10
paddle_height = 60
paddle_speed = 5
ball_speed = 3
ball_max_speed = 8
ball_min_speed = 3
player_score = 0
ai_score = 0

# Create paddles
player_paddle = pygame.Rect(0, HEIGHT // 2 - paddle_height // 2, paddle_width, paddle_height)
ai_paddle = pygame.Rect(WIDTH - paddle_width, HEIGHT // 2 - paddle_height // 2, paddle_width, paddle_height)

# Create ball
ball = pygame.Rect(WIDTH // 2 - ball_radius // 2, HEIGHT // 2 - ball_radius // 2, ball_radius, ball_radius)
ball_angle = random.uniform(-math.pi / 4, math.pi / 4)
ball_speed_x = ball_speed * math.cos(ball_angle)
ball_speed_y = ball_speed * math.sin(ball_angle)

# Function to update the score on the screen
def draw_score():
    font = pygame.font.Font(None, FONT_SIZE)
    text = font.render(f"Player: {player_score}    AI: {ai_score}", True, FONT_COLOR)
    text_rect = text.get_rect(center=(WIDTH // 2, FONT_SIZE))
    screen.blit(text, text_rect)

# Function to update the paddles' positions
def update_paddles():
    player_paddle.y += paddle_speed * player_paddle_direction
    ai_paddle.y += paddle_speed * ai_paddle_direction

    # Keep the paddles inside the screen
    player_paddle.y = max(min(player_paddle.y, HEIGHT - paddle_height), 0)
    ai_paddle.y = max(min(ai_paddle.y, HEIGHT - paddle_height), 0)
# Function to update the ball's position
def update_ball():
    global player_score, ai_score, ball_speed_x, ball_speed_y

    ball.x += ball_speed_x
    ball.y += ball_speed_y

    # Check collision with paddles
    if ball.colliderect(player_paddle):
        delta_y = ball.centery - player_paddle.centery
        ball_angle = math.pi / 4 * (delta_y / (paddle_height / 2))
        ball_speed = math.hypot(ball_speed_x, ball_speed_y)
        ball_speed_x = ball_speed * math.cos(ball_angle)
        ball_speed_y = ball_speed * math.sin(ball_angle)

        ball_speed_x = abs(ball_speed_x)  # Ensure the ball always moves towards the AI paddle

        # Increase ball speed if paddle is moving in the same direction
        if player_paddle_direction * ball_speed_y > 0:
            ball_speed_y *= 1.2
        # Decrease ball speed if paddle is moving in the opposite direction
        elif player_paddle_direction * ball_speed_y < 0:
            ball_speed_y /= 1.2

        ball_speed_y = max(min(ball_speed_y, ball_max_speed), -ball_max_speed)

    elif ball.colliderect(ai_paddle):
        delta_y = ball.centery - ai_paddle.centery
        ball_angle = math.pi - math.pi / 4 * (delta_y / (paddle_height / 2))
        ball_speed = math.hypot(ball_speed_x, ball_speed_y)
        ball_speed_x = ball_speed * math.cos(ball_angle)
        ball_speed_y = ball_speed * math.sin(ball_angle)

        ball_speed_x = -abs(ball_speed_x)  # Ensure the ball always moves towards the player paddle

        # Increase ball speed if paddle is moving in the same direction
        if ai_paddle_direction * ball_speed_y > 0:
            ball_speed_y *= 1.2
        # Decrease ball speed if paddle is moving in the opposite direction
        elif ai_paddle_direction * ball_speed_y < 0:
            ball_speed_y /= 1.2

        ball_speed_y = max(min(ball_speed_y, ball_max_speed), -ball_max_speed)

    # Check collision with walls
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_speed_y = -ball_speed_y

    # Check if the ball went out of bounds
    if ball.left <= 0:
        ai_score += 1
        reset_ball()
    elif ball.right >= WIDTH:
        player_score += 1
        reset_ball()


# Function to reset the ball's position and speed
def reset_ball():
    ball.center = (WIDTH // 2, HEIGHT // 2)
    ball_angle = random.uniform(-math.pi / 4, math.pi / 4)
    ball_speed_x = ball_speed * math.cos(ball_angle)
    ball_speed_y = ball_speed * math.sin(ball_angle)

# Game loop
running = True
player_paddle_direction = 0
ai_paddle_direction = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Control the player paddle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                player_paddle_direction = -1
            elif event.key == pygame.K_DOWN:
                player_paddle_direction = 1
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                player_paddle_direction = 0

    # AI Player logic
    if ai_paddle.top < ball.y:
        ai_paddle_direction = 1
    elif ai_paddle.bottom > ball.y:
        ai_paddle_direction = -1
    else:
        ai_paddle_direction = 0

    # Update game elements
    update_paddles()
    update_ball()

    # Fill the screen
    screen.fill(BLACK)

    # Draw paddles and ball
    pygame.draw.rect(screen, WHITE, player_paddle)
    pygame.draw.rect(screen, WHITE, ai_paddle)
    pygame.draw.ellipse(screen, WHITE, ball)

    # Draw score
    draw_score()

    # Update the display
    pygame.display.flip()

    # Set the frame rate
    clock.tick(FPS)

# Quit the game
pygame.quit()

