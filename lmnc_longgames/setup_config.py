import os, time, threading, sys
from typing import List
import pygame
from multiverse_game import MultiverseGame
from multiverse import Display
from config import LongGameConfig

BLACK = (0, 0, 0)

class SetupConfigGame(MultiverseGame):

    def __init__(self):
        upscale_factor = 6
        super().__init__("Configure", 120, upscale_factor)
        self.menu_select_state = False
        # Put a number on every serial device detected
        try:
            serial_dir = r'/dev/serial/by-id'
            self.found_devices = [f'{serial_dir}/{file}' for file in os.listdir(serial_dir)]
        except FileNotFoundError as e:
            print(f'Error getting serial devices: {e}')
            print('Check your serial configuration, and make sure udev rules are configured correctly (i.e. 60-serial.rules)')
            sys.exit(-1)
        #self.found_devices = [f'{serial_dir}/{file}' for file in [1,2,3,4,5,6,7,8,9]]
        if not len(self.found_devices):
            print("No serial devices found!")
            return

        self.reconfigure_displays()
    
    def reconfigure_displays(self):
        
        # Delete the old displays
        # if self.multiverse_display:
        #     old_displays = self.multiverse_display.displays
        #     for old_display in old_displays:
        #         old_display.__del__()
        
        # Create new displays

        if self.multiverse_display:
            self.multiverse_display.stop()

        print('Found the following serial devices:')
        displays = []
        for i, file in enumerate(self.found_devices):
            print(f'{i}: {file}')
            displays.append(Display(f'{file}', 53, 11, 0, 11 * i))
        print("")
        
        self.configure_display(displays)


    def game_loop_callback(self, events: List, dt: float):

        self.pygame_screen.fill(BLACK)

        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
        
        for i, file in enumerate(self.found_devices):
            position = len(self.found_devices) - 1 - i
            self.display_number(i)

    def display_number(self, screen_number:int):
        script_path = os.path.realpath(os.path.dirname(__file__))
        font = pygame.font.Font(f"{script_path}/Amble-Bold.ttf", 10 * self.upscale_factor)
        text = font.render(f"{screen_number}", False, (255, 255, 255))
        text = pygame.transform.rotate(text, -90)

        self.pygame_screen.blit(text, [((screen_number * 11)) * self.upscale_factor, 10 * self.upscale_factor])

    def prompt_for_display_order(self):
        time.sleep(1)
        getting_input = True
        while getting_input:
            val = input("Is the order from left (lowest) to right (highest) correct (y/n)? ")
            if val.lower().startswith("y"):
                print("Great, saving config")
                
                config = LongGameConfig()
                config.config['displays']['main']['devices'] = self.found_devices
                config.write()
                getting_input = False
                self.stop()
            else:
                #prompt for the numbers/order
                val = input("From left to right, input the numbers that you see on each display, separated by commas: ")
                new_order = [x.strip() for x in val.split(',')]
                print(new_order)
                new_order.reverse()
                reversed_devices = self.found_devices[::-1]
                self.found_devices = [reversed_devices[int(i)] for i in new_order]

                self.reconfigure_displays()


    # Generate a list of IDs for the config in the correct order

def main():
    game = SetupConfigGame()
    input_thread = threading.Thread(target=game.prompt_for_display_order, args=[])
    game_thread = threading.Thread(target=game.run, args=[])

    game_thread.start()
    input_thread.start()
    game_thread.join()
    #TODO: Signal to interrupt input if the game was quit?
    input_thread.join()


if __name__ == "__main__":
    main()