import numpy
import serial
import threading


# Class to represent a single Galactic Unicorn display
# handy place to store the serial port opening and such
class Display:
    # Just in case we get fancy and use RGB565 or RGB332
    BYTES_PER_PIXEL = 4

    def __init__(self, port, w, h, x, y):
        self.path = port
        self.port = None
        self.w = w
        self.h = h
        self.x = x
        self.y = y

    def setup(self):
        self.port = serial.Serial(self.path)

    def write(self, buffer):
        if self.port is None:
            return
        self.port.write(buffer[self.y:self.y + self.h, self.x:self.x + self.w].tobytes())

    def flush(self):
        if self.port is None:
            return
        self.port.flush()

    def update(self, buffer):
        threading.Thread(target=self.write, args=(buffer,)).start()

    def __del__(self):
        if self.port is None:
            return
        # Clear the displays to black when the program bails
        self.port.write(numpy.zeros((self.w, self.h, self.BYTES_PER_PIXEL), dtype=numpy.uint8).tobytes())
        self.port.flush()
        self.port.close()


class Multiverse:
    def __init__(self, *args):
        self.displays = list(args)

    def setup(self):
        for display in self.displays:
            display.setup()

    def add(self, display):
        self.displays.append(display)

    def update(self, buffer):
        for display in self.displays:
            display.update(buffer)

        for display in self.displays:
            display.flush()