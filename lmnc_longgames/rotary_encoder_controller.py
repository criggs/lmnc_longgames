from typing import Callable
from RPi import GPIO
from time import sleep
from threading import Thread

class RotaryEncoderController:
    def __init__(self, event_callback: Callable[[int,int], None], positive_event_id: int = 1, negative_event_id: int = -1, clk: int = 22, dt: int = 27, switch: int = 17):
        self.clk = clk
        self.dt = dt
        self.switch = switch
        self.event_callback = event_callback
        self.positive_event_id = positive_event_id
        self.negative_event_id = negative_event_id

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.running = False

    def start(self):
        self.running = True
        self.counter = 0
        self.clkLastState = GPIO.input(self.clk)
        self.controller_thread = Thread(target=self.run, args=[])
        self.controller_thread.start()

    def stop(self):
        self.running = False
        self.controller_thread.join()

    def run(self):
        try:

            while self.running:
                self.clkState = GPIO.input(self.clk)
                self.dtState = GPIO.input(self.dt)
                if self.clkState != self.clkLastState:
                    if self.dtState != self.clkState:
                        self.counter += 1
                        self.event_callback(self.positive_event_id, self.counter)
                    else:
                        self.counter -= 1
                        self.event_callback(self.negative_event_id, self.counter)
                self.clkLastState = self.clkState
                sleep(0.001)
        finally:
            GPIO.cleanup()


def main():
    def callback(event_id, counter):
        print(f'{"increased to " if event_id > 0 else "decreased to "} {counter}')

    controller = RotaryEncoderController(callback)
    controller.start()
    controller.controller_thread.join()

if __name__ == "__main__":
    main()