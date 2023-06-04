import os
import signal
import time
import sys
import threading
from typing import List
import pygame
import numpy
from config import LongGameConfig
from multiverse import Multiverse, Display

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

FONT_SIZE = 11
FONT_COLOR = WHITE

MODE_ONE_PLAYER = 1
MODE_TWO_PLAYER = 2
MODE_AI_VS_AI = 3


class MultiverseGame:
    """
    Pygame Instance with display duplication to a multiverse display (collection of unicorn displays)
    
    Handles the execution of a menu loop and a game loop.
    
    The menu loop will select between 3 different game modes.
    
    The game loop will draw the next frame of the game. The dt will be passed into this loop so frame independant math can be used.
    
    """


    MODE_ONE_PLAYER = 1
    MODE_TWO_PLAYER = 2
    MODE_AI_VS_AI = 3

    def __init__(self, 
                 game_title: str, 
                 fps: int, 
                 upscale_factor: int,
                 headless: bool = False
            ) -> None:
        if headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        pygame.display.set_caption(game_title)
        self.clock = pygame.time.Clock()
        self.headless = headless
        script_path = os.path.realpath(os.path.dirname(__file__))
        self.font = pygame.font.Font(f"{script_path}/Amble-Bold.ttf", FONT_SIZE * upscale_factor)
        self.game_title = game_title
        self.fps = fps
        self.width = 0
        self.height = 0
        self.upscale_factor = upscale_factor
        self.multiverse_display = None
        self.pygame_screen = None
        self.dt = 0
        self.exit_flag = threading.Event()
        self.menu_select_state = True
        self.game_mode = 1
        self.initial_configure_called = False
        
        print(f'Initializing game {self.game_title}')
        print(f'fps: {fps}')
        print(f'upscale_factor: {upscale_factor}')

        signal.signal(signal.SIGINT, self.signal_handler)


    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C!')
        self.stop()
        sys.exit(0)


    def game_mode_callback(self, game_mode: int):
        """
        Override this method for game mode selection
        """
        pass

    def game_loop_callback(self, events, dt):
        """
        Override this method for the game loop
        """
        pass

    def reset_game_callback(self):

        """
        Override this method for game reset
        """
        pass

    def configure_display(self, displays: List[Display] = []):
        
        if not len(displays):
            #Load the defaults from the config
            config = LongGameConfig()
            displays = [Display(f'{file}', 53, 11, 0, 11 * i) for i, file in enumerate(config.config['displays']['main']['devices'] )]
            
        self.multiverse_display = Multiverse(*displays)
        self.multiverse_display.setup()
        self.multiverse_display.start() # Starts the execution thread for the buffer
        self.width = len(self.multiverse_display.displays) * 11 * self.upscale_factor
        self.height = 53 * self.upscale_factor
        print(f'Upscaled Width: {self.width} Upscaled Height: {self.height}')
        
        if not self.initial_configure_called:
            self.pygame_screen = pygame.display.set_mode((self.width, self.height))
            if self.headless:
                # From: https://stackoverflow.com/a/14473777
                # surface alone wouldn't work so I needed to add a rectangle
                self.pygame_screen = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
                pygame.draw.rect(self.pygame_screen, (0,0,0), (0, 0, self.width, self.height), 0)
            self.initial_configure_called = True

    def flip_display(self):
        pygame.display.flip()
        framegrab = pygame.surfarray.array2d(self.pygame_screen)
        downsample = numpy.array(framegrab)[::self.upscale_factor, ::self.upscale_factor]
        # We need to reorder the rows for the correct origin/pixel position on the individual displays
        downsample = numpy.flipud(downsample)
        self.multiverse_display.update(downsample)

    def stop(self):
        #TODO fix possible race conditions when stopping in the middle of a loop function
        self.pygame_screen.fill(BLACK)
        self.flip_display()
        self.exit_flag.set()
        self.multiverse_display.stop()
        pygame.quit()

    def reset(self):
        if self.reset_game_callback:
            self.reset_game_callback()
        self.menu_select_state = True
        self.pygame_screen.fill(BLACK)

    """
    Runs the game loop.
    
    """
    def run(self):
        self.exit_flag.clear()
        prev_time = time.time()

        while not self.exit_flag.wait(0.001):
            now = time.time()
            self.dt = now - prev_time
            prev_time = now

            # Get all events
            events = pygame.event.get()

            #TODO: Make the controls work with GPIO/Joysticks    
            # Check for quit
            for event in events:
                if event.type == pygame.QUIT:
                    self.exit_flag.set()
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_q:
                    self.exit_flag.set()
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_r:
                    self.reset()

            # TODO Add some game states and make this a switch for the state
            if self.game_mode_callback and self.menu_select_state:
                self.menu_loop(events)
                if not self.menu_select_state:
                    self.display_countdown()
                    prev_time = time.time()
            else:
                self.game_loop_callback(events, self.dt)
            # Update the display
            self.flip_display()

            # Set the frame rate
            self.clock.tick(self.fps)

        print("Ended multiverse game run loop")
        self.stop()

    """
    Game mode selection menu
    """
    def menu_loop(self, events):
        # Check for menu selection
        for event in events:
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_1:
                    self.game_mode = 1
                    self.menu_select_state = False
                if event.key == pygame.K_2:
                    self.game_mode = 2
                    self.menu_select_state = False
                if event.key == pygame.K_3:
                    self.game_mode = 3
                    self.menu_select_state = False

        if self.headless:
            self.game_mode = 3
            self.menu_select_state = False
            print("Hack to select AI mode, until the menu has a way to headlessly select a game mode")

        if not self.menu_select_state:
            self.game_mode_callback(self.game_mode)

        # Display the menu
        # Fill the screen
        self.pygame_screen.fill(BLACK)

        title_text = self.font.render("Select Game Mode", False, WHITE)
        mode1_text = self.font.render("1. 1 Player", False, WHITE)
        mode2_text = self.font.render("2. 2 Players", False, WHITE)
        mode3_text = self.font.render("3. AI vs AI", False, WHITE)


        center_screen = self.width // 2
        self.pygame_screen.blit(title_text, (center_screen - title_text.get_width() // 2, 5 * self.upscale_factor))
        self.pygame_screen.blit(
            mode1_text, (center_screen - mode1_text.get_width() // 2, 15 * self.upscale_factor))
        self.pygame_screen.blit(
            mode2_text, (center_screen - mode2_text.get_width() // 2, 25 * self.upscale_factor))
        self.pygame_screen.blit(
            mode3_text, (center_screen - mode3_text.get_width() // 2, 35 * self.upscale_factor))

    def display_countdown(self):
        print("Starting countdown...")
        for i in range(3, 0, -1):
            print(i)
            self.pygame_screen.fill(BLACK)
            countdown_text = self.font.render(str(i), False, WHITE)
            self.pygame_screen.blit(countdown_text, (self.width // 4 - countdown_text.get_width() // 2, self.height // 2 - countdown_text.get_height() // 2))
            self.pygame_screen.blit(countdown_text, (3 * self.width // 4 - countdown_text.get_width() // 2, self.height // 2 - countdown_text.get_height() // 2))
            self.flip_display()
            pygame.time.wait(1000)
        print("GO!")
