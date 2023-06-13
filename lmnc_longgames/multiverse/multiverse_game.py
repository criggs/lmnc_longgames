import os, signal, time, sys, threading, getopt

try:
    import RPi.GPIO as gpio

    print("Running on a Raspberry PI")
except (ImportError, RuntimeError):
    print("Not running on a Raspberry PI. Setting mock GPIO Zero Pin Factory.")
    os.environ["GPIOZERO_PIN_FACTORY"] = "mock"

from typing import List
from enum import Enum
import pygame
import numpy
from lmnc_longgames.config import LongGameConfig
from lmnc_longgames.multiverse.multiverse import Multiverse, Display
from lmnc_longgames.util.rotary_encoder_controller import RotaryEncoderController
from lmnc_longgames.util.screen_power_reset import ScreenPowerReset
from lmnc_longgames.constants import *
from gpiozero import Button


FONT_SIZE = 11
FONT_COLOR = WHITE


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

        print(f"Initializing multiverse display")
        print(f"upscale_factor: {upscale_factor}")

    def configure_display(self, displays: List[Display] = []):
        if not len(displays):
            # Load the defaults from the config
            config = LongGameConfig()
            dummy_displays = config.config["displays"]["main"].get("dummy", False)
            displays = [
                Display(f"{file}", 53, 11, 0, 11 * i, dummy=dummy_displays)
                for i, file in enumerate(config.config["displays"]["main"]["devices"])
            ]

        self.multiverse = Multiverse(*displays)
        self.multiverse.start()  # Starts the execution thread for the buffer
        self.width = len(self.multiverse.displays) * 11 * self.upscale_factor
        self.height = 53 * self.upscale_factor
        print(f"Upscaled Width: {self.width} Upscaled Height: {self.height}")

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
        pygame.display.flip()
        # This is a copy of the pixels into a new array
        framegrab = pygame.surfarray.array2d(self.pygame_screen)
        downsample = numpy.array(framegrab)[
            :: self.upscale_factor, :: self.upscale_factor
        ]
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

    def __init__(
        self, game_title: str, fps: int, multiverse_display: PygameMultiverseDisplay
    ) -> None:
        self.multiverse_display = multiverse_display
        script_path = os.path.realpath(os.path.dirname(__file__))
        self.font = pygame.freetype.Font(f"{script_path}/../icl8x8u.bdf")
        self.game_title = game_title
        self.fps = fps
        self.menu_select_state = True
        self.game_mode = 1

        print(f"Initializing game {self.game_title}")
        print(f"fps: {fps}")

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

    def display_countdown(self):
        print("Starting countdown...")
        for i in range(3, 0, -1):
            print(i)
            self.screen.fill(BLACK)
            countdown_text, _ = self.font.render(str(i), WHITE)
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
        print("GO!")


class MenuItem:
    def __init__(self, name: str, children: list = None, props: dict = {}):
        self.name = name
        self.children = children
        self.props = props
        self.highlighted_index = 0
        self.parent = None
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
        self.multiverse_display = PygameMultiverseDisplay(
            "Multiverse Games", upscale_factor, headless
        )
        self.multiverse_display.configure_display()
        self.clock = pygame.time.Clock()
        self.game = None
        self.menu_inactive_start_time = time.time()
        script_path = os.path.realpath(os.path.dirname(__file__))
        self.font = pygame.freetype.Font(f"{script_path}/../icl8x8u.bdf", size=8)

        # P1 Controller
        RotaryEncoderController(
            controller_id=P1,
            event_callback=self.fire_controller_input_event,
            clk_pin=22,
            dt_pin=27,
            rotary_push_button_pin=17,
            a_button_pin=9,
            b_button_pin=10,
        )
        # P2 Controller
        RotaryEncoderController(
            controller_id=P2,
            event_callback=self.fire_controller_input_event,
            clk_pin=25,
            dt_pin=24,
            rotary_push_button_pin=23,
            a_button_pin=7,
            b_button_pin=8,
        )

        # TODO: Console Controls (Restart, back to menu, etc)

        from lmnc_longgames.games.longpong import LongPongGame
        from lmnc_longgames.games.snake import SnakeGame
        from lmnc_longgames.demos.fire_demo import FireDemo
        from lmnc_longgames.demos.matrix_demo import MatrixDemo
        from lmnc_longgames.demos.life_demo import LifeDemo

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
                MenuItem(
                    "Demos",
                    [
                        MenuItem("Fire", props={"constructor": FireDemo}),
                        MenuItem("Matrix", props={"constructor": MatrixDemo}),
                        MenuItem("Life", props={"constructor": LifeDemo}),
                        MenuItem("Back"),
                    ],
                ),
            ],
        )

        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("You pressed Ctrl+C!")
        if self.exit_flag.is_set():
            print("Force closing")
            sys.exit(1)
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
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYUP and event.key == pygame.K_q
                ):
                    # TODO: Add a physical button?
                    self.exit_flag.set()
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

                # Jump directly into a specific game, skipping the menu. These could be physical buttons
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
                    from lmnc_longgames.games.longpong import LongPongGame

                    self.game = LongPongGame(self.multiverse_display)
                    continue

            if self.game is None:
                # Show game selection menu
                self.menu_loop(events, self.dt)
            else:
                self.game.loop(events, self.dt)
            # Update the display
            self.multiverse_display.flip_display()

            # Set the frame rate
            self.clock.tick(self.game.fps if self.game is not None else 120)

        print("Ended multiverse game run loop")
        self.stop()

    def start_random_game(self):
        # TODO make this a random selection
        from life_demo_game import LifeDemoGame

        self.game = LifeDemoGame(self.multiverse_display)

    def select_menu_item(self):
        selected_child = self.game_menu.children[self.game_menu.highlighted_index]
        if selected_child.name == "Back":
            selected_child = self.game_menu.parent
        if selected_child.children is None:
            game_name = selected_child.name
            print(f"Selected menu leaf {game_name}")

            args = selected_child.props.get("args", [])
            self.game = selected_child.props["constructor"](
                self.multiverse_display, *args
            )
        else:
            self.game_menu = selected_child

    def menu_loop(self, events, dt):
        elapsed_menu_time = time.time() - self.menu_inactive_start_time
        if elapsed_menu_time > MAX_MENU_INACTIVE_TIME:
            print(
                f"Menu time elapsed, starting random demo after {MAX_MENU_INACTIVE_TIME} seconds"
            )
            self.start_random_game()
            return

        highlight_change = 0
        for event in events:
            # See if something is selected
            if (event.type == pygame.KEYUP and event.key == pygame.K_RETURN) or (
                event.type == BUTTON_RELEASED and event.input == ROTARY_PUSH
            ):
                self.menu_inactive_start_time = time.time()
                self.select_menu_item()
            # See if we moved, increase/decrease highlighting
            if (event.type == pygame.KEYUP and event.key == pygame.K_UP) or (
                event.type == ROTATED_CCW
            ):
                self.menu_inactive_start_time = time.time()
                highlight_change = -1
            if (event.type == pygame.KEYUP and event.key == pygame.K_DOWN) or (
                event.type == ROTATED_CW
            ):
                self.menu_inactive_start_time = time.time()
                highlight_change = 1

        self.game_menu.highlight(self.game_menu.highlighted_index + highlight_change)

        # Show the current menu
        to_display = self.game_menu.get_display_list()

        screen = self.multiverse_display.pygame_screen
        width = self.multiverse_display.width
        upscale_factor = self.multiverse_display.upscale_factor

        screen.fill(BLACK)
        center_screen = width // 2

        title_text, _ = self.font.render(f"__{self.game_menu.name}__", WHITE)
        title_text = pygame.transform.scale_by(title_text, upscale_factor)
        screen.blit(
            title_text,
            (center_screen - title_text.get_width() // 2, 5 * upscale_factor),
        )

        render_index = 0
        for i, child in to_display:
            text = child.name
            child_text, _ = self.font.render(text, WHITE)
            child_text = pygame.transform.scale_by(child_text, upscale_factor)
            text_x = center_screen - child_text.get_width() // 2
            text_y = (15 + (10 * render_index)) * upscale_factor
            screen.blit(child_text, (text_x, text_y))

            if self.game_menu.highlighted_index == i:
                indicator_text, _ = self.font.render(">", WHITE)
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
            print("multiverse_game.py [-w] [-d]")
            sys.exit()
        elif opt == "-w":
            show_window = True
        elif opt == "-d":
            debug = True

    upscale_factor = 5 if show_window else 1

    game_main = MultiverseMain(upscale_factor, headless=not show_window)

    # Set up control buttons

    def back_to_menu():
        event = pygame.event.Event(
            BUTTON_RELEASED, {"controller": 0, "input": BUTTON_MENU}
        )
        pygame.event.post(event)

    game_menu_button = Button(20)
    game_menu_button.when_released = back_to_menu

    def reset_game():
        event = pygame.event.Event(
            BUTTON_RELEASED, {"controller": 0, "input": BUTTON_RESET}
        )
        pygame.event.post(event)

    game_reset_button = Button(21)
    game_reset_button.when_released = reset_game

    ScreenPowerReset(reset_pin=PIN_RESET_RELAY, button_pin=16)

    game_main.run()


if __name__ == "__main__":
    main()
