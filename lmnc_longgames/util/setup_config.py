import os, time, threading, sys, getopt, signal
from typing import List
import pygame
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame, PygameMultiverseDisplay
from lmnc_longgames.multiverse import Display
from lmnc_longgames.config import LongGameConfig

BLACK = (0, 0, 0)


class SetupConfigGame(MultiverseGame):
    def __init__(self, multiverse_display: PygameMultiverseDisplay):
        super().__init__("Configure", 60, multiverse_display)
        self.getting_input = True
        # Put a number on every serial device detected
        try:
            serial_dir = r"/dev/serial/by-id"
            self.found_devices = [
                f"{serial_dir}/{file}" for file in os.listdir(serial_dir)
            ]
        except FileNotFoundError as e:
            print(f"Error getting serial devices: {e}")
            print(
                "Check your serial configuration, and make sure udev rules are configured correctly (i.e. 60-serial.rules)"
            )
            sys.exit(-1)
        # self.found_devices = [f'{serial_dir}/{file}' for file in [1,2,3,4,5,6,7,8,9]]
        if not len(self.found_devices):
            print("No serial devices found!")
            return

        self.reconfigure_displays()

    def reconfigure_displays(self):
        if self.multiverse_display:
            self.multiverse_display.stop()

        print("Found the following serial devices:")
        displays = []
        for i, file in enumerate(self.found_devices):
            print(f"{i}: {file}")
            displays.append(Display(f"{file}", 53, 11, 0, 11 * i))
        print("")

        self.multiverse_display.configure_display(displays)

    def loop(self, events: List, dt: float):
        self.screen.fill(BLACK)

        for i, file in enumerate(self.found_devices):
            position = len(self.found_devices) - 1 - i
            self.display_number(i)

    def display_number(self, screen_number: int):
        script_path = os.path.realpath(os.path.dirname(__file__))
        font = pygame.freetype.Font(f"{script_path}/../icl8x8u.bdf", size=8)

        text, _ = self.font.render(f"{screen_number}", (255,255,255))
        text = pygame.transform.scale_by(text, self.upscale_factor)
        text = pygame.transform.rotate(text, -90)

        self.screen.blit(
            text,
            [((screen_number * 11) + 2) * self.upscale_factor, 25 * self.upscale_factor],
        )

    def prompt_for_display_order(self):
        time.sleep(1)
        while self.getting_input:
            val = input(
                "Is the order from left (lowest) to right (highest) correct (y/n)? "
            )
            if val.lower().startswith("y"):
                print("Great, saving config")

                config = LongGameConfig()
                config.config["displays"]["main"]["devices"] = self.found_devices
                config.write()
                self.getting_input = False

                event = pygame.event.Event(pygame.QUIT)
                pygame.event.post(event)
            else:
                # prompt for the numbers/order
                val = input(
                    "From left to right, input the numbers that you see on each display, separated by commas: "
                )
                new_order = [x.strip() for x in val.split(",")]
                print(new_order)
                new_order.reverse()
                reversed_devices = self.found_devices[::-1]
                self.found_devices = [reversed_devices[int(i)] for i in new_order]

                self.reconfigure_displays()


class SetupConfigMain:
    """
    Program to initialize displays, show game menu, and execute games
    """

    def __init__(self, upscale_factor, headless):
        self.exit_flag = threading.Event()
        self.multiverse_display = PygameMultiverseDisplay(
            "Multiverse Games", upscale_factor, headless
        )
        self.multiverse_display.configure_display([])
        self.clock = pygame.time.Clock()
        self.game = SetupConfigGame(self.multiverse_display)

        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("You pressed Ctrl+C!")
        self.game.getting_input = False
        if self.exit_flag.is_set():
            print("Force closing")
            sys.exit(1)
        self.stop()
        sys.exit(0)

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

            self.game.loop(events, self.dt)
            # Update the display
            self.multiverse_display.flip_display()

            # Set the frame rate
            self.clock.tick(self.game.fps)

        print("Ended multiverse game run loop")
        self.stop()


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

    upscale_factor = 1 if show_window else 1

    game_main = SetupConfigMain(upscale_factor, headless=not show_window)

    input_thread = threading.Thread(
        target=game_main.game.prompt_for_display_order, args=[]
    )
    input_thread.start()

    game_main.run()
    input_thread.join()


if __name__ == "__main__":
    main()
