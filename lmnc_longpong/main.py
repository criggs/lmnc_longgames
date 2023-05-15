import pygame
import random
import math

# Contants
UPSCALE_FACTOR = 5

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

class Ball:
    def __init__(self, radius: int) -> None:
        self.radius = radius
        self.direction_y = -1
        self.direction_x = 1
        self.speed = 1
        self.angle = 0
        self.rect = pygame.Rect(WIDTH // 2 - self.radius // 2, HEIGHT // 2 - self.radius // 2, self.radius, self.radius)
        
    def reset(self):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.angle = random.uniform(-math.pi / 4, math.pi / 4)
        self.speed = 2 * UPSCALE_FACTOR
    
    @property
    def speed_x(self):
        return self.speed * math.cos(self.angle) * self.direction_x
    
    @property
    def speed_y(self):
        return self.speed * math.sin(self.angle) * self.direction_y

# Initialize Pygame
pygame.init()

# Set up the game window

font = pygame.font.Font("lmnc_longpong/Amble-Bold.ttf", FONT_SIZE)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()

# Game variables
ball_radius = 2 * UPSCALE_FACTOR
paddle_width = 2 * UPSCALE_FACTOR
paddle_height = 10 * UPSCALE_FACTOR

player_paddle_speed = 3 * UPSCALE_FACTOR
ai_paddle_speed = 2 * UPSCALE_FACTOR

ball_max_speed = 10 * UPSCALE_FACTOR
ball_min_speed = 2 * UPSCALE_FACTOR

# Create paddles
player_one = Player(pygame.Rect(0, HEIGHT // 2 - paddle_height // 2, paddle_width, paddle_height))
player_two = Player(pygame.Rect(WIDTH - paddle_width, HEIGHT // 2 - paddle_height // 2, paddle_width, paddle_height))

# Create ball
ball = Ball(2 * UPSCALE_FACTOR)

# Function to update the score on the screen
def draw_score():
    global font
    text = font.render(f"P1: {player_one.score}    P2: {player_two.score}", True, FONT_COLOR)
    text_rect = text.get_rect(center=(WIDTH // 2, FONT_SIZE))
    screen.blit(text, text_rect)

def update_paddle(player: Player):
    speed = player_paddle_speed
    if player.is_ai:
        update_for_ai(player)
        #Only use the slower ai speed if one player is human
        speed = ai_paddle_speed if player_one.is_ai != player_two.is_ai else player_paddle_speed
    player.rect.y += speed * player.direction
    player.rect.y = max(min(player.rect.y, HEIGHT - paddle_height), 0)

def update_for_ai(ai_player: Player):
    if ball.direction_x != ai_player.position or abs(ball.rect.centerx - ai_player.rect.centerx) > WIDTH // 2:
        ai_player.direction = 0
        return
    
    # AI Player logic
    if ai_player.rect.centery < ball.rect.centery - paddle_height // 2:
        ai_player.direction = 1
    elif ai_player.rect.centery > ball.rect.centery + paddle_height // 2:
        ai_player.direction = -1
    else:
        ai_player.direction = 0

# Function to update the ball's position
def update_ball():
    ball.rect.x += ball.speed_x
    ball.rect.y += ball.speed_y

    # Detect Left Paddle Collision
    left_collision = ball.rect.left <= paddle_width and (abs(ball.rect.centery - player_one.rect.centery) <= paddle_height//2)
    
    # Detect Right Paddle Collision
    right_collision = ball.rect.right >= WIDTH - paddle_width and (abs(ball.rect.centery - player_two.rect.centery) <= paddle_height//2)

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
        player_two.score += 1
        ball.reset()
    elif ball.rect.left >= WIDTH:
        player_one.score += 1
        ball.reset()

def update_ball_speed_from_collision(colliding_player: Player):
    delta_y = ball.rect.centery - colliding_player.rect.centery
    ball.angle = math.pi / 4 * (delta_y / (paddle_height / 2))

    # Increase ball speed if paddle is moving in the same direction
    if colliding_player.direction * ball.speed_y > 0:
        ball.speed *= 1.2
    # Decrease ball speed if paddle is moving in the opposite direction
    elif colliding_player.direction * ball.speed_y < 0:
        ball.speed /= 1.2
    # Reverse the direction of travel
    ball.direction_x = colliding_player.position * -1
    
# Function to display the countdown
def display_countdown():
    global font
    for i in range(3, 0, -1):
        screen.fill(BLACK)
        countdown_text = font.render(str(i), True, WHITE)
        screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT // 2 - countdown_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.wait(1000)

def reset_game():
    global running, player_one, player_two, ball
    running = True
    
    screen.fill(BLACK)

    display_countdown()
    ball.reset()
    player_one.reset()
    player_two.reset()
    
    player_one.is_ai = True
    player_two.is_ai = True

reset_game()

# Game loop
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
            if event.key == pygame.K_r:
                reset_game()

    # Update game elements
    update_paddle(player_one)
    update_paddle(player_two)
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

