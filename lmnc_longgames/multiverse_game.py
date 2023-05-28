import os
import time
from typing import Callable, List
import pygame
import numpy
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

    def __init__(self, 
                 game_title: str, 
                 fps: int, 
                 upscale_factor: int, 
                 game_mode_callback: Callable[[int],None],
                 game_loop_callback: Callable[[List,float],None], 
                 reset_game_callback: Callable[[],None]
            ) -> None:
        pygame.init()
        pygame.display.set_caption(game_title)
        self.clock = pygame.time.Clock()

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
        self.running = False
        self.menu_select_state = True
        self.game_mode_callback = game_mode_callback
        self.game_loop_callback = game_loop_callback
        self.reset_game_callback = reset_game_callback
        self.game_mode = 1
        
        print(f'Initializing game {self.game_title}')
        print(f'fps: {fps}')
        print(f'upscale_factor: {upscale_factor}')

    def configure_display(self):
        #TODO Test the displays, make this configurable
        self.multiverse_display = Multiverse(
            Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_E66118604B503C27-if00", 53, 11, 0, 0),
            Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 11),
            Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 22),
            Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 33),
            Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 44),
            Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 55),
            Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 66),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 77),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 88),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 99),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 110),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 121),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 132),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 143),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 154),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 165),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 176),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 187),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 198),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 209),
            # Display("/dev/serial/by-id/usb-Raspberry_Pi_Picoprobe_XXXXXXXXXXXXXXXX-if00", 53, 11, 0, 220)
        )
        self.multiverse_display.setup()
        self.width = len(self.multiverse_display.displays) * 11 * self.upscale_factor
        self.height = 53 * self.upscale_factor
        print(f'Upscaled Width: {self.width} Upscaled Height: {self.height}')
        self.pygame_screen = pygame.display.set_mode((self.width, self.height))

    def flip_display(self):
        pygame.display.flip()
        # TODO: Grab the frame buffer, downsample with a numpy slice, pass to the multiverse. Do we need to convert?
        framegrab = pygame.surfarray.array2d(self.pygame_screen)
        downsample = numpy.array(framegrab)[::self.upscale_factor, ::self.upscale_factor]
        # Update the displays from the buffer
        
        # The display will be inverted without this
        downsample = numpy.flipud(downsample)
        self.multiverse_display.update(downsample)

    def stop(self):
        self.running = False

    def reset(self):
        self.reset_game_callback()
        self.menu_select_state = True
        self.pygame_screen.fill(BLACK)

    """
    Runs the game loop.
    
    """
    def run(self):
        self.running = True
        prev_time = time.time()

        while self.running:
            now = time.time()
            self.dt = now - prev_time
            prev_time = now

            # Get all events
            events = pygame.event.get()

            #TODO: Make the controls work with GPIO/Joysticks    
            # Check for quit
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_q:
                    self.running = False
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_r:
                    self.reset()

            # TODO Add some game states and make this a switch for the state
            if self.menu_select_state:
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

        # Quit the game
        pygame.quit()

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

        if not self.menu_select_state:
            self.game_mode_callback(self.game_mode)

        # Display the menu
        # Fill the screen
        self.pygame_screen.fill(BLACK)

        title_text = self.font.render("Select Game Mode", True, WHITE)
        mode1_text = self.font.render("1. 1 Player", True, WHITE)
        mode2_text = self.font.render("2. 2 Players", True, WHITE)
        mode3_text = self.font.render("3. AI vs AI", True, WHITE)


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
            countdown_text = self.font.render(str(i), True, WHITE)
            self.pygame_screen.blit(countdown_text, (self.width // 4 - countdown_text.get_width() // 2, self.height // 2 - countdown_text.get_height() // 2))
            self.pygame_screen.blit(countdown_text, (3 * self.width // 4 - countdown_text.get_width() // 2, self.height // 2 - countdown_text.get_height() // 2))
            self.flip_display()
            pygame.time.wait(1000)
        print("GO!")
