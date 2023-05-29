import os, time, threading
from typing import List
import pygame
from multiverse_game import MultiverseGame
from multiverse import Display

BLACK = (0, 0, 0)

class SetupConfigGame(MultiverseGame):

    def __init__(self):
        upscale_factor = 6
        super().__init__("Configure", 120, upscale_factor)
        self.menu_select_state = False
        # Put a number on every serial device detected
        serial_dir = r'/dev/serial/by-id'
        #found_devices = os.listdir(serial_dir)
        self.found_devices = [1,2,3,4,5,6,7,8,9]
        if not len(self.found_devices):
            print("No serial devices found!")
            return

        
        print('Found the following serial devices:')
        for file in self.found_devices:
            print(file)
        print("")

        displays = [Display(f'{serial_dir}/{file}', 53, 11, 0, 11 * i) for i, file in enumerate(self.found_devices)]
        self.configure_display(displays)


    def game_loop_callback(self, events: List, dt: float):

        self.pygame_screen.fill(BLACK)
        
        for i, file in enumerate(self.found_devices):
            self.display_number(i)

    def display_number(self, screen_number:int):
        script_path = os.path.realpath(os.path.dirname(__file__))
        font = pygame.font.Font(f"{script_path}/Amble-Bold.ttf", 10 * self.upscale_factor)
        text = font.render(f"{screen_number}", True, (255, 255, 255))
        text = pygame.transform.rotate(text, -90)

        self.pygame_screen.blit(text, [((screen_number * 11)) * self.upscale_factor, 10 * self.upscale_factor])

    def prompt_for_display_order(self):
        time.sleep(1)
        getting_input = True
        while getting_input:
            val = input("Is the order from left (lowest) to right (highest) correct (y/n)? ")
            if val.lower().startswith("y"):
                print("Great, saving config")
                getting_input = False
                self.stop()
            else:
                #prompt for the numbers/order
                val = input("From left to right, input the numbers that you see on each display, separated by commas: ")
                new_order = [x.strip() for x in val.split(',')]
                print(new_order)
                #TODO Actually recalculate the order and update the displayed screens/numbers


    # Generate a list of IDs for the config in the correct order

def main():
    game = SetupConfigGame()
    input_thread = threading.Thread(target=game.prompt_for_display_order, args=[])
    # starting thread 1
    input_thread.start()
    game.run()
    input_thread.join()


if __name__ == "__main__":
    main()