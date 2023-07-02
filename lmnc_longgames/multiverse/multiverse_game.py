import os, signal, time, sys, threading, getopt
import logging

try:
    import RPi.GPIO as gpio

    logging.info("Running on a Raspberry PI")
except (ImportError, RuntimeError):
    logging.info("Not running on a Raspberry PI. Setting mock GPIO Zero Pin Factory.")
    os.environ["GPIOZERO_PIN_FACTORY"] = "mock"

import random
from typing import List
from enum import Enum
import pygame
import numpy
from lmnc_longgames.config import LongGameConfig
from lmnc_longgames.multiverse import Multiverse, Display
from lmnc_longgames.util.rotary_encoder_controller import RotaryEncoderController
from lmnc_longgames.util.screen_power_reset import ScreenPowerReset
from lmnc_longgames.constants import *
from gpiozero import Button, DigitalOutputDevice


font_SIZE = 11
font_COLOR = WHITE


class PygameMultiverseDisplay:
    def __init__(
        self, display_title: str, upscale_factor: int, headless: bool = False
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
        self.mute = False
        self.sound_trigger_out = DigitalOutputDevice(PIN_TRIGGER_OUT)
        self.flip_count = 0

        logging.info(f"Initializing multiverse display")
        logging.info(f"upscale_factor: {upscale_factor}")

    def configure_display(self, displays: List[Display] = None):
        if displays is None:
            # Load the defaults from the config
            config = LongGameConfig()
            dummy_displays = config.config["displays"]["main"].get("dummy", False)
            displays = [
                Display(f"{file}", 53, 11, 0, 11 * i, dummy=(dummy_displays or 'dummy' in file))
                for i, file in enumerate(config.config["displays"]["main"]["devices"])
            ]

        self.multiverse = Multiverse(*displays)
        self.multiverse.setup(use_threads=True)  # Starts the execution thread for the buffer
        self.width = len(self.multiverse.displays) * 11 * self.upscale_factor
        self.height = 53 * self.upscale_factor
        logging.info(f"Upscaled Width: {self.width} Upscaled Height: {self.height}")

        if not self.initial_configure_called:
            self.pygame_screen = pygame.display.set_mode(
                (self.width, self.height), depth=32
            )
            if self.headless:
                # From: https://stackoverflow.com/a/14473777
                # surface alone wouldn't work so I needed to add a rectangle
                # self.pygame_screen = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
                pygame.draw.rect(
                    self.pygame_screen, (0, 0, 0), (0, 0, self.width, self.height), 0
                )
            self.initial_configure_called = True

    def flip_display(self):

        start = time.time()
        pygame.display.flip()
        elapsed = time.time() - start

        if self.flip_count % 100 == 0:
            logging.debug(f'pygame flip took {elapsed * 1000} ms')

        start = time.time()
        # This is a copy of the pixels into a new array
        framegrab = pygame.surfarray.array2d(self.pygame_screen)
        downsample = numpy.array(framegrab)[
            :: self.upscale_factor, :: self.upscale_factor
        ]
        # We need to reorder the rows for the correct origin/pixel position on the individual displays
        downsample = numpy.flipud(downsample)
        elapsed = time.time() - start
        if self.flip_count % 100 == 0:
            logging.debug(f'downsample took {elapsed * 1000} ms')

        
        start = time.time()
        self.multiverse.update(downsample)
        elapsed = time.time() - start
        if self.flip_count % 100 == 0:
            logging.debug(f'multiverse update took {elapsed * 1000} ms')

        self.flip_count += 1

    def play_note(self, *args, **kwargs):
        #Trigger out, even if the screens are muted
        self.sound_trigger_out.blink(on_time=TRIGGER_OUT_ON_TIME, n=1)

        if self.mute:
            return
        self.multiverse.play_note(*args, **kwargs)
        #self.multiverse.play_note(0, 55, phase=Display.PHASE_OFF)

    def stop(self):
        self.multiverse.stop()
        
    def reset(self):
        self.multiverse.reset()

class GameObject:
    def __init__(self, game):
        self.game = game
        self._rect = pygame.Rect(0,0,0,0)
        self._x = 0.0
        self._y = 0.0
    
    
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
    
    @property
    def width(self):
        return self._rect.width
    
    @width.setter
    def width(self, w):
        self._rect.width = w
        
    @property
    def height(self):
        return self._rect.height
    
    @height.setter
    def height(self, h):
        self._rect.height = h
        
    def update(self, dt: float):
        pass

    def draw(self, screen):
        pass
    
    def reset(self):
        pass
    
    def collides_with(self, other_object):
        return self._rect.colliderect(other_object._rect)

class MultiverseGame:
    """
    Pygame Instance with display duplication to a multiverse display (collection of unicorn displays)

    Handles the execution of a menu loop and a game loop.

    The menu loop will select between 3 different game modes.

    The game loop will draw the next frame of the game. The dt will be passed into this loop so frame independent math can be used.

    """

    def __init__(
        self, game_title: str, fps: int, multiverse_display: PygameMultiverseDisplay, fixed_fps = False
    ) -> None:
        self.multiverse_display = multiverse_display
        script_path = os.path.realpath(os.path.dirname(__file__))
        self.font = pygame.font.Font(f"{script_path}/../icl8x8u.bdf", 8)
        self.game_title = game_title
        self.fps = fps
        self.fixed_fps = fixed_fps
        self.frame_count = 0
        self.menu_select_state = True
        self.game_mode = 1
        self.reset_input_history(P1)
        self.reset_input_history(P2)
        self.exit_game_flag = False

        logging.info(f"Initializing game {self.game_title}")
        logging.info(f"fps: {fps}")

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
    
    def play_note(self, *args, **kwargs):
        self.multiverse_display.play_note(*args, **kwargs)

    def update_history(self, controller, event):
        history = self.p1_input_history if controller == P1 else self.p2_input_history
        if event[0] in [ROTATED_CW, ROTATED_CCW] and history[-1] == event:
            #Only record a single movement event for multiple moves in the same direction
            return
        history.pop(0)
        history.append(event)
    
    def has_history(self, controller, to_check):
        history = self.p1_input_history if controller == P1 else self.p2_input_history
        history_slice  = history[-len(to_check):]
        return history_slice == to_check

    def exit_game(self):
        self.exit_game_flag = True

    def loop(self, events, dt):
        """1    
        Override this method for the game loop
        """
        for event in events:
            if event.type in [ROTATED_CW, ROTATED_CCW, BUTTON_RELEASED]:
                self.update_history(event.controller, (event.type, event.input))

    def reset(self):
        """
        Override this method for game reset
        """
        self.reset_input_history(P1)
        self.reset_input_history(P2)

    def reset_input_history(self, controller):
        if controller == P1:
            self.p1_input_history = [0] * 20
        else:
            self.p2_input_history = [0] * 20

    def random_note(self, waveform=64):
        self.play_note(0, PENTATONIC[random.randint(4*5,5*5)], waveform=waveform)

    def death_note(self):
        self.play_note(0, 55, release=1000, waveform=32)
        self.play_note(1, 60, release=1000, waveform=32)
        self.play_note(2, 65, release=1000, waveform=32)
        self.play_note(3, 70, release=1000, waveform=32)

    def win_note(self):
        self.play_note(0, 880, release=1000, waveform=32)
        self.play_note(1, 440, release=1000, waveform=32)
        self.play_note(2, 220, release=1000, waveform=32)
        self.play_note(4, 110, release=1000, waveform=32)

    def display_countdown(self):
        logging.info("Starting countdown...")
        for i in range(3, 0, -1):
            logging.info(i)
            self.screen.fill(BLACK)
            countdown_text = self.font.render(str(i), False, WHITE)
            countdown_text = pygame.transform.scale_by(
                countdown_text, self.upscale_factor
            )

            self.screen.blit(
                countdown_text,
                (
                    self.width // 4 - countdown_text.get_width() // 2,
                    self.height // 2 - countdown_text.get_height() // 2,
                ),
            )
            self.screen.blit(
                countdown_text,
                (
                    3 * self.width // 4 - countdown_text.get_width() // 2,
                    self.height // 2 - countdown_text.get_height() // 2,
                ),
            )
            self.multiverse_display.flip_display()
            pygame.time.wait(1000)
        logging.info("GO!")


class MenuItem:
    def __init__(self, name: str, children: list = None, props: dict = {}, parent = None):
        self.name = name
        self.children = children
        self.props = props
        self.highlighted_index = 0
        self.parent = parent
        if children is not None:
            for child in children:
                child.parent = self

    def highlight(self, index):
        if index < 0:
            index = len(self.children) - 1
        elif index >= len(self.children):
            index = 0
        self.highlighted_index = index

    def get_display_list(self):
        """
        Return 3 list items, containing the highlighted item
        """
        l = len(self.children)

        min_index = max(0, self.highlighted_index - 1)
        max_index = min(min_index + 3, l - 1)
        r = range(min_index, max_index + 1)
        return [(i, self.children[i]) for i in r]


class MultiverseMain:
    """
    Program to initialize displays, show game menu, and execute games
    """

    def __init__(self, upscale_factor, headless):
        self.exit_flag = threading.Event()
        self._sig_handler_called=False
        self.multiverse_display = PygameMultiverseDisplay(
            "Multiverse Games", upscale_factor, headless
        )
        self.multiverse_display.configure_display()
        self.clock = pygame.time.Clock()
        self.game = None
        self.menu_inactive_start_time = time.time()
        self.running_demo = False
        self.demo_start_time = self.menu_inactive_start_time
        script_path = os.path.realpath(os.path.dirname(__file__))
        self.font = pygame.font.Font(f"{script_path}/../icl8x8u.bdf", size=8)

        config = LongGameConfig()

        # P1 Controller
        RotaryEncoderController(
            controller_id=P1,
            event_callback=self.fire_controller_input_event,
            clk_pin=PIN_P1_CLK,
            dt_pin=PIN_P1_DT,
            rotary_push_button_pin=PIN_P1_ROT_PUSH,
            a_button_pin=PIN_P1_A,
            b_button_pin=PIN_P1_B,
        )
        # P2 Controller
        RotaryEncoderController(
            controller_id=P2,
            event_callback=self.fire_controller_input_event,
            clk_pin=PIN_P2_CLK,
            dt_pin=PIN_P2_DT,
            rotary_push_button_pin=PIN_P2_ROT_PUSH,
            a_button_pin=PIN_P2_A,
            b_button_pin=PIN_P2_B,
        )

        # TODO: Console Controls (Restart, back to menu, etc)

        from lmnc_longgames.games.longpong import LongPongGame
        from lmnc_longgames.games.snake import SnakeGame
        from lmnc_longgames.games.breakout import BreakoutGame

        from lmnc_longgames.demos.fire_demo import FireDemo
        from lmnc_longgames.demos.matrix_demo import MatrixDemo
        from lmnc_longgames.demos.life_demo import LifeDemo
        from lmnc_longgames.demos.video_demo import VideoDemo
        from lmnc_longgames.demos.marquee_demo import MarqueeDemo
        from lmnc_longgames.games.invaders import InvadersGame

        self.game_menu = MenuItem(
            "Long Games",
            [
                MenuItem(
                    "Long Pong",
                    [
                        MenuItem(
                            "1 Player", props={"constructor": LongPongGame, "args": [1]}
                        ),
                        MenuItem(
                            "2 Player", props={"constructor": LongPongGame, "args": [2]}
                        ),
                        MenuItem(
                            "AI vs AI", props={"constructor": LongPongGame, "args": [0]}
                        ),
                        MenuItem("Back"),
                    ],
                ),
                MenuItem("Snake", props={"constructor": SnakeGame}),
                MenuItem("Breakout", props={"constructor": BreakoutGame}),
                MenuItem("Invaders", props={"constructor": InvadersGame}),
                MenuItem(
                    "Demos",
                    [
                        MenuItem("Fire", props={"constructor": FireDemo}),
                        MenuItem("Matrix", props={"constructor": MatrixDemo}),
                        MenuItem("Life", props={"constructor": LifeDemo}),
                        MenuItem("Back"),
                    ],
                )
            ],
        )


        '''
        Videos are configured in .config/lmnc_longgames/config.json, i.e.:
        {
            ...
            "videos": [
                {"name":"My Video", "path": "/my/cool/video.mp4"}
            ]
            ...
        }
        '''
        video_config = config.config.get("videos",[])

        video_items = [MenuItem(v.get('name'), props={"constructor": VideoDemo, "args":[v.get('path')]}) for v in video_config]
        if(len(video_items)):
            video_items.append(MenuItem("Back"))
            self.game_menu.children.append(MenuItem("Videos", video_items, parent=self.game_menu))

        self.game_menu.children.append(MenuItem("Special Thanks", parent=self.game_menu, props={"constructor": MarqueeDemo, "args": ["Special Thanks"]}))
        
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        logging.info("You pressed Ctrl+C!")
        if self._sig_handler_called:
            logging.info("Force closing")
            sys.exit(1)
        self._sig_handler_called = True
        self.stop()
        sys.exit(0)

    def fire_controller_input_event(
        self, event_id: int, controller_id: int, input_id: int
    ):
        event = pygame.event.Event(
            event_id, {"controller": controller_id, "input": input_id}
        )
        pygame.event.post(event)

    def set_selected_game(self, game: MultiverseGame):
        self.game = game
        self.game.display = self.multiverse_display

    def stop(self):
        logging.debug("Stopping Game")
        self.exit_flag.set()
        logging.debug("Stopping Multiverse")
        self.multiverse_display.stop()
        logging.debug("Quitting Pygamse")
        pygame.quit()

    """
    Runs the game loop.
    
    """

    def run(self):
        self.exit_flag.clear()
        previous_frame_start_time = time.time()

        game_start_time = None

        while not self.exit_flag.wait(0.001):
            
            frame_start_time = time.time()
            self.dt = frame_start_time - previous_frame_start_time
            previous_frame_start_time = frame_start_time

            if self.game is not None and self.game.exit_game_flag:
                self.game = None
                game_start_time = None
                self.menu_inactive_start_time = time.time()
                self.running_demo = False

            if self.running_demo and frame_start_time > (self.demo_start_time + DEMO_SWITCH_TIME):
                #change the demo
                self.load_demo_disc()


            start = time.time()
            # Get all events
            events = pygame.event.get()

            # Check for quit
            for event in events:
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYUP and event.key == pygame.K_q
                ):
                    # TODO: Add a physical button?
                    self.exit_flag.set()
                    continue
                if self.running_demo and event.type in [pygame.KEYUP, BUTTON_RELEASED, ROTATED_CW, ROTATED_CCW]:
                    self.game = None
                    self.menu_inactive_start_time = time.time()
                    self.running_demo = False
                    continue
                if (
                    event.type == pygame.KEYUP
                    and event.key == pygame.K_r
                    or (event.type == BUTTON_RELEASED and event.input == BUTTON_RESET)
                ):
                    self.game.reset()
                    continue
                if (event.type == pygame.KEYUP and event.key == pygame.K_m) or (
                    event.type == BUTTON_RELEASED and event.input == BUTTON_MENU
                ):
                    self.game = None
                    self.menu_inactive_start_time = time.time()
                    continue
            elapsed = time.time() - start
            if self.game is not None and self.game.frame_count % 100 == 0:
                logging.debug(f'pygame events took {elapsed * 1000} ms')

            if self.game is None:
                game_start_time = None
                # Show game selection menu
                self.menu_loop(events, self.dt)
            else:

                start = time.time()
                if game_start_time is None:
                    game_start_time = time.time()
                    frame_start_time = game_start_time
                    self.game.frame_count = 0
                self.game.loop(events, self.dt)
                elapsed = time.time() - start
                if self.game is not None and self.game.frame_count % 100 == 0:
                    logging.debug(f'game loop took {elapsed * 1000} ms')

                self.game.frame_count += 1
                
            # Update the display            
            start = time.time()
            self.multiverse_display.flip_display()
            elapsed = time.time() - start
            
            if self.game is not None and self.game.frame_count % 100 == 1:
                logging.debug(f'flip_display took {elapsed * 1000} ms')

            frame_elapsed_time = time.time() - frame_start_time

            if self.game is not None and self.game.frame_count % 100 == 1:
                logging.debug(f'frame_elapsed_time took {frame_elapsed_time * 1000} ms')

            if self.game is not None and game_start_time is not None:
                game_elapsed_time = time.time() - game_start_time
                observed_fps = self.game.frame_count / game_elapsed_time
                if self.game.frame_count % 100 == 1:
                    logging.debug(f"Observed FPS: {observed_fps}")

                if  self.game.fixed_fps:
                    # Hacky attempt to keep a fixed-ish framerate
                    # Added specifically for video playback
                    fps_delay = 1000/(self.game.fps + 5)
                    frame_draw_delay = frame_elapsed_time * 1000
                    sync_offset = 0
                    if(observed_fps < self.game.fps):
                        #speed up
                        sync_offset = - fps_delay / 2
                    elif observed_fps > self.game.fps:
                        #slow down
                        sync_offset = fps_delay / 2
                        
                    actual_delay = max(0, fps_delay - frame_draw_delay + sync_offset)
                    
                    if self.game.frame_count % 100 == 1:
                        logging.debug(f'FPS Delay: {fps_delay}, frame_draw_delay: {frame_draw_delay}, actual_delay: {actual_delay}')                        
                    
                    pygame.time.delay(int(actual_delay))
                    #time.sleep(actual_delay / 1000)
                else: # Basic frame limiting
                    # Set the frame rate
                    self.clock.tick(self.game.fps if self.game is not None else 120)
            else:
                # No game right now, not sure why were here but lets keep that train a' rolling
                self.clock.tick(120)

        logging.info("Ended multiverse game run loop")
        self.stop()

    def load_demo_disc(self):
        from lmnc_longgames.demos.fire_demo import FireDemo
        from lmnc_longgames.demos.matrix_demo import MatrixDemo
        from lmnc_longgames.demos.life_demo import LifeDemo
        from lmnc_longgames.games.longpong import LongPongGame
        from lmnc_longgames.demos.marquee_demo import MarqueeDemo

        options = [
            (LongPongGame, [0]),
            (FireDemo, []),
            (MatrixDemo, []),
            (LifeDemo, []),
            (MarqueeDemo, ["Special Thanks"]),
        ]
        game_class, args = random.choice(options)

        self.game = game_class(self.multiverse_display, *args)
        self.demo_start_time = time.time()
        self.running_demo = True

    def select_menu_item(self):
        selected_child = self.game_menu.children[self.game_menu.highlighted_index]
        if selected_child.name == "Back":
            selected_child = self.game_menu.parent
        if selected_child.children is None:
            game_name = selected_child.name
            logging.info(f"Selected menu leaf {game_name}")

            args = selected_child.props.get("args", [])
            self.game = selected_child.props["constructor"](
                self.multiverse_display, *args
            )
            self.game_menu = selected_child.parent
        else:
            self.game_menu = selected_child

    def menu_loop(self, events, dt):
        elapsed_menu_time = time.time() - self.menu_inactive_start_time
        if elapsed_menu_time > MAX_MENU_INACTIVE_TIME:
            logging.info(
                f"Menu time elapsed, starting random demo after {MAX_MENU_INACTIVE_TIME} seconds"
            )
            self.load_demo_disc()
            return

        highlight_change = 0
        for event in events:
            # See if something is selected
            if (event.type == pygame.KEYUP and event.key == pygame.K_RETURN) or (
                event.type == BUTTON_RELEASED and event.input in [ROTARY_PUSH, BUTTON_A]
            ):
                self.menu_inactive_start_time = time.time()
                self.select_menu_item()
                self.multiverse_display.play_note(0, C_MINOR[8*3], waveform=64)
            # See if we moved, increase/decrease highlighting
            if (event.type == pygame.KEYUP and event.key == pygame.K_UP) or (
                event.type == ROTATED_CCW
            ):
                self.menu_inactive_start_time = time.time()
                highlight_change = -1
                self.multiverse_display.play_note(0, C_MINOR[8*2], waveform=64)
            if (event.type == pygame.KEYUP and event.key == pygame.K_DOWN) or (
                event.type == ROTATED_CW
            ):
                self.menu_inactive_start_time = time.time()
                highlight_change = 1
                self.multiverse_display.play_note(0, C_MINOR[8*2], waveform=64)


        self.game_menu.highlight(self.game_menu.highlighted_index + highlight_change)

        # Show the current menu
        to_display = self.game_menu.get_display_list()

        screen = self.multiverse_display.pygame_screen
        width = self.multiverse_display.width
        upscale_factor = self.multiverse_display.upscale_factor

        screen.fill(BLACK)
        center_screen = width // 2

        title_text = self.font.render(f"__{self.game_menu.name}__", False, WHITE)
        title_text = pygame.transform.scale_by(title_text, upscale_factor)
        screen.blit(
            title_text,
            (center_screen - title_text.get_width() // 2, 5 * upscale_factor),
        )

        render_index = 0
        for i, child in to_display:
            text = child.name
            child_text = self.font.render(text, False, WHITE)
            child_text = pygame.transform.scale_by(child_text, upscale_factor)
            text_x = center_screen - child_text.get_width() // 2
            text_y = (15 + (10 * render_index)) * upscale_factor
            screen.blit(child_text, (text_x, text_y))

            if self.game_menu.highlighted_index == i:
                indicator_text = self.font.render(">", False, WHITE)
                indicator_text = pygame.transform.scale_by(
                    indicator_text, upscale_factor
                )
                screen.blit(indicator_text, (text_x - (10 * upscale_factor), text_y))

            render_index += 1


def main():
    # Constants/Configuration
    show_window = False
    debug = False
    opts, args = getopt.getopt(sys.argv[1:], "hwd", [])
    for opt, arg in opts:
        if opt == "-h":
            logging.info("multiverse_game.py [-w] [-d]")
            sys.exit()
        elif opt == "-w":
            show_window = True
        elif opt == "-d":
            debug = True




    root = logging.getLogger()
    if debug:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    logging.info("Starting LonGame Program")
    upscale_factor = 5 if show_window else 1

    game_main = MultiverseMain(upscale_factor, headless=not show_window)

    # Set up control buttons

    def mute_display():
        logging.info("Muting Display")
        game_main.multiverse_display.mute = True

    def unmute_display():
        logging.info("Un-muting Display")
        game_main.multiverse_display.mute = False

    mute_switch = Button(PIN_SWITCH_MUTE)
    mute_switch.when_pressed = mute_display
    mute_switch.when_released = unmute_display

    if mute_switch.is_pressed:
        mute_display()
    else:
        unmute_display()

    def back_to_menu():
        event = pygame.event.Event(
            BUTTON_RELEASED, {"controller": 0, "input": BUTTON_MENU}
        )
        pygame.event.post(event)

    game_menu_button = Button(PIN_BUTTON_MENU)
    game_menu_button.when_released = back_to_menu

    def reset_game():
        event = pygame.event.Event(
            BUTTON_RELEASED, {"controller": 0, "input": BUTTON_RESET}
        )
        pygame.event.post(event)

    game_reset_button = Button(PIN_BUTTON_GAME_RESET)
    game_reset_button.when_released = reset_game

    #ScreenPowerReset(reset_pin=PIN_RESET_RELAY, button_pin=PIN_BUTTON_SCREEN_RESET)

    def reset_screen():
        logging.info("Reset Screens Button Pressed.")
        try:
            game_main.stop()
            game_main.multiverse_display.reset()
        finally:
            logging.info("Stopping program. Should restart if running as a service")
            sys.exit(2)
    screen_reset_button = Button(PIN_BUTTON_SCREEN_RESET)
    screen_reset_button.when_released = reset_screen
    
    try:
        game_main.run()
    except Exception as e:
        logging.error("Exception from Game Main Run. Stopping Program.", exc_info=e)
        game_main.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
