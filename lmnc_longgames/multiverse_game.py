import os, signal, time, sys, threading, getopt

try:
    import RPi.GPIO as gpio
    print("Running on a Raspberry PI")
except (ImportError, RuntimeError):
    print("Not running on a Raspberry PI. Setting mock GPIO Zero Pin Factory.")
    os.environ["GPIOZERO_PIN_FACTORY"] = "mock"

from typing import List
import pygame
import numpy
from config import LongGameConfig
from multiverse import Multiverse, Display
from rotary_encoder_controller import RotaryEncoderController
from screen_power_reset import ScreenPowerReset


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

FONT_SIZE = 11
FONT_COLOR = WHITE

MODE_ONE_PLAYER = 1
MODE_TWO_PLAYER = 2
MODE_AI_VS_AI = 3

class PygameMultiverseDisplay:
    def __init__(self, 
                 display_title: str, 
                 upscale_factor: int,
                 headless: bool = False
            ) -> None:
        if headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        pygame.display.set_caption(display_title)
        self.headless = headless
        self.width = 0
        self.height = 0
        self.upscale_factor = upscale_factor
        self.multiverse = None
        self.pygame_screen = None
        self.initial_configure_called = False
        
        print(f'Initializing multiverse display')
        print(f'upscale_factor: {upscale_factor}')
        
        
    def configure_display(self, displays: List[Display] = []):
        
        if not len(displays):
            #Load the defaults from the config
            config = LongGameConfig()
            dummy_displays = config.config['displays']['main'].get("dummy", False)
            displays = [Display(f'{file}', 53, 11, 0, 11 * i, dummy=dummy_displays) for i, file in enumerate(config.config['displays']['main']['devices'] )]
            
        self.multiverse = Multiverse(*displays)
        self.multiverse.start() # Starts the execution thread for the buffer
        self.width = len(self.multiverse.displays) * 11 * self.upscale_factor
        self.height = 53 * self.upscale_factor
        print(f'Upscaled Width: {self.width} Upscaled Height: {self.height}')
        
        if not self.initial_configure_called:
            self.pygame_screen = pygame.display.set_mode((self.width, self.height), depth=32)
            if self.headless:
                # From: https://stackoverflow.com/a/14473777
                # surface alone wouldn't work so I needed to add a rectangle
                #self.pygame_screen = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
                pygame.draw.rect(self.pygame_screen, (0,0,0), (0, 0, self.width, self.height), 0)
            self.initial_configure_called = True

    def flip_display(self):
        pygame.display.flip()
        #This is a copy of the pixels into a new array
        framegrab = pygame.surfarray.array2d(self.pygame_screen)
        downsample = numpy.array(framegrab)[::self.upscale_factor, ::self.upscale_factor]
        # We need to reorder the rows for the correct origin/pixel position on the individual displays
        downsample = numpy.flipud(downsample)
        self.multiverse.update(downsample)
        
    def stop(self):
        self.multiverse.stop()

class MultiverseGame:
    """
    Pygame Instance with display duplication to a multiverse display (collection of unicorn displays)
    
    Handles the execution of a menu loop and a game loop.
    
    The menu loop will select between 3 different game modes.
    
    The game loop will draw the next frame of the game. The dt will be passed into this loop so frame independent math can be used.
    
    """



    P1_UP = pygame.USEREVENT + 1 
    P1_DOWN = P1_UP + 1
    P1_SELECT = P1_DOWN + 1
    P1_A = P1_SELECT + 1
    P1_B = P1_A + 1

    P2_UP = P1_B + 1 
    P2_DOWN = P2_UP + 1
    P2_SELECT = P2_DOWN + 1
    P2_A = P2_SELECT + 1
    P2_B = P2_A + 1

    MODE_ONE_PLAYER = 1
    MODE_TWO_PLAYER = 2
    MODE_AI_VS_AI = 3

    def __init__(self, 
                 game_title: str, 
                 fps: int, 
                 multiverse_display: PygameMultiverseDisplay
            ) -> None:
            
        self.multiverse_display = multiverse_display
        script_path = os.path.realpath(os.path.dirname(__file__))
        self.font = pygame.font.Font(f"{script_path}/Amble-Bold.ttf", FONT_SIZE * self.multiverse_display.upscale_factor)
        self.game_title = game_title
        self.fps = fps
        self.menu_select_state = True
        self.game_mode = 1
        
        print(f'Initializing game {self.game_title}')
        print(f'fps: {fps}')


    @property
    def upscale_factor(self):
        return self.multiverse_display.upscale_factor

    @property
    def height(self):
        return self.multiverse_display.height
        
    @property
    def width(self):
        return self.multiverse_display.width
        
    @property
    def screen(self):
        return self.multiverse_display.pygame_screen

    @property
    def display_count(self):
        return len(self.multiverse_display.multiverse.displays)

    def game_mode_callback(self, game_mode: int):
        """
        Override this method for game mode selection
        """
        pass

    def loop(self, events, dt):
        """
        Override this method for the game loop
        """
        pass

    def reset(self):

        """
        Override this method for game reset
        """
        pass

    """
    Game mode selection menu
    """
    def menu_loop(self, events):
        # Check for menu selection
        # for event in events:
        #     if event.type == pygame.KEYUP:
        #         if event.key == pygame.K_1:
        #             self.game_mode = 1
        #             self.menu_select_state = False
        #         if event.key == pygame.K_2:
        #             self.game_mode = 2
        #             self.menu_select_state = False
        #         if event.key == pygame.K_3:
        #             self.game_mode = 3
        #             self.menu_select_state = False

        # if self.headless:
        #     self.game_mode = 3
        #     self.menu_select_state = False
        #     print("Hack to select AI mode, until the menu has a way to headlessly select a game mode")

        self.game_mode = 3
        self.menu_select_state = False
        if not self.menu_select_state:
            self.game_mode_callback(self.game_mode)

        # Display the menu
        # Fill the screen
        self.screen.fill(BLACK)

        title_text = self.font.render("Select Game Mode", False, WHITE)
        mode1_text = self.font.render("1. 1 Player", False, WHITE)
        mode2_text = self.font.render("2. 2 Players", False, WHITE)
        mode3_text = self.font.render("3. AI vs AI", False, WHITE)


        center_screen = self.width // 2
        self.screen.blit(title_text, (center_screen - title_text.get_width() // 2, 5 * self.upscale_factor))
        self.screen.blit(
            mode1_text, (center_screen - mode1_text.get_width() // 2, 15 * self.upscale_factor))
        self.screen.blit(
            mode2_text, (center_screen - mode2_text.get_width() // 2, 25 * self.upscale_factor))
        self.screen.blit(
            mode3_text, (center_screen - mode3_text.get_width() // 2, 35 * self.upscale_factor))

    def display_countdown(self):
        print("Starting countdown...")
        for i in range(3, 0, -1):
            print(i)
            self.screen.fill(BLACK)
            countdown_text = self.font.render(str(i), False, WHITE)
            self.screen.blit(countdown_text, (self.width // 4 - countdown_text.get_width() // 2, self.height // 2 - countdown_text.get_height() // 2))
            self.screen.blit(countdown_text, (3 * self.width // 4 - countdown_text.get_width() // 2, self.height // 2 - countdown_text.get_height() // 2))
            self.multiverse_display.flip_display()
            pygame.time.wait(1000)
        print("GO!")


        
class MultiverseMain:
    '''
    Program to initialize displays, show game menu, and execute games
    '''
    def __init__(self, upscale_factor, headless):
        self.exit_flag = threading.Event()
        self.multiverse_display = PygameMultiverseDisplay("Multiverse Games", upscale_factor, headless)
        self.multiverse_display.configure_display()
        self.clock = pygame.time.Clock()
        self.game = None
        
        #P1 Controller
        RotaryEncoderController(self.fire_controller_input_event, 
                                                positive_event_id=MultiverseGame.P1_UP, 
                                                negative_event_id=MultiverseGame.P1_DOWN, 
                                                clk_pin = 22, 
                                                dt_pin = 27, 
                                                button_pin = 17)
        #P2 Controller
        RotaryEncoderController(self.fire_controller_input_event, 
                                                positive_event_id=MultiverseGame.P2_UP, 
                                                negative_event_id=MultiverseGame.P2_DOWN, 
                                                clk_pin = 25, 
                                                dt_pin = 24, 
                                                button_pin = 23)
        
        
    
        signal.signal(signal.SIGINT, self.signal_handler)
    
    
    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C!')
        if self.exit_flag.is_set():
            print("Force closing")
            sys.exit(1)
        self.stop()
        sys.exit(0)
    
    def fire_controller_input_event(self, event_id: int):
        event = pygame.event.Event(event_id)
        pygame.event.post(event)
        
    def set_selected_game(self, game: MultiverseGame):
        self.game = game
        self.game.display = self.multiverse_display
    
    def stop(self):
        self.multiverse_display.pygame_screen.fill(BLACK)
        self.multiverse_display.flip_display()
        self.exit_flag.set()
        self.multiverse_display.stop()
        pygame.quit()

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
            
            # Check for quit
            for event in events:
                if event.type == pygame.QUIT:
                    self.exit_flag.set()
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_q:
                    self.exit_flag.set()
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_r:
                    self.game.reset()
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_1:     
                    from fire_demo_game import FireDemoGame
                    self.game = FireDemoGame(self.multiverse_display)
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_2:     
                    from matrix_demo_game import MatrixDemoGame
                    self.game = MatrixDemoGame(self.multiverse_display)
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_3:     
                    from life_demo_game import LifeDemoGame
                    self.game = LifeDemoGame(self.multiverse_display)
                    continue
                if event.type == pygame.KEYUP and event.key == pygame.K_4:     
                    from longpong import LongPongGame
                    self.game = LongPongGame(self.multiverse_display)
                    continue
                
                
            if self.game is None:
                #Show game selection menu
                self.menu_loop(events, self.dt)
            else:
                self.game.loop(events, self.dt)
            # Update the display
            self.multiverse_display.flip_display()

            # Set the frame rate
            self.clock.tick(self.game.fps)

        print("Ended multiverse game run loop")
        self.stop()
        

    def menu_loop(self, events, dt):
        #TODO: Hack until a real menu selection is added
        from longpong import LongPongGame
        self.game = LongPongGame(self.multiverse_display)




def main():
    # Constants/Configuration
    show_window = False
    debug = False
    opts, args = getopt.getopt(sys.argv[1:],"hwd",[])
    for opt, arg in opts:
        if opt == '-h':
            print ('multiverse_game.py [-w] [-d]')
            sys.exit()
        elif opt == '-w':
            show_window = True
        elif opt == '-d':
            debug = True
    
    upscale_factor = 5 if show_window else 1

    game_main = MultiverseMain(upscale_factor, headless = not show_window)

    ScreenPowerReset(reset_pin=26, button_pin=16)
    
    game_main.run()


if __name__ == "__main__":
    main()


