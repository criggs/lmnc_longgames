import numpy
import serial
import threading
import signal
import time
import struct


__version__ = '0.0.2'

# Class to represent a single Galactic Unicorn display
# handy place to store the serial port opening and such
class Display:
    # Just in case we get fancy and use RGB565 or RGB332
    BYTES_PER_PIXEL = 4

    WAVEFORM_NOISE = 128
    WAVEFORM_SQUARE = 64
    WAVEFORM_SAW = 32
    WAVEFORM_TRIANGLE = 16
    WAVEFORM_SINE = 8
    WAVEFORM_WAVE = 1

    PHASE_ATTACK = 0
    PHASE_DECAY = 1
    PHASE_SUSTAIN = 2
    PHASE_RELEASE = 3
    PHASE_OFF = 4

    def __init__(self, port, w, h, x, y, rotate=0, dummy=False):
        self.path = port
        self.port = None
        self.w = w
        self.h = h
        self.x = x
        self.y = y
        self.rotate = int(rotate / 90)
        self._use_threads = False
        self.dummy = dummy

    def setup(self, use_threads=False):
        if self.dummy:
            # Nothing to do here, move along
            return
        self.port = serial.Serial(self.path)
    
        self._use_threads = use_threads
        if self._use_threads:
            self._running = True
            self._buffer = bytearray(self.w * self.h * self.BYTES_PER_PIXEL)
            self._event = threading.Event()
            self._thread = threading.Thread(target=self._update_thread).start()

    def write(self, buffer):
        if self.port is None:
            return
        self.port.write(b"multiverse:data")
        self.port.write(buffer)
        self.port.flush()

    def _update_thread(self):
        while self._running:
            if not self._event.wait(0.1):
                continue
            self.write(self._buffer)
            self._event.clear()

    def bootloader(self):
        if self.port is None:
            return
        if self._use_threads:
            self._running = False
            self.sync()
        self.port.write(b"multiverse:_usb")
        self.port.flush()

    def reset(self):
        if self.port is None:
            return
        if self._use_threads:
            self._running = False
            self.sync()
        self.port.write(b"multiverse:_rst")
        self.port.flush()

    def play_note(self, channel, frequency, waveform=WAVEFORM_TRIANGLE, attack=10, decay=200, sustain=0, release=0, phase=PHASE_ATTACK):
        self.sync()
        self.port.write(b"multiverse:note")
        self.port.write(struct.pack("<BHBHHHHB", channel, frequency, waveform, attack, decay, sustain, release, phase))
        self.port.flush()

    def update(self, buffer):
        buffer = numpy.rot90(buffer[self.y:self.y + self.h, self.x:self.x + self.w], self.rotate).tobytes()
        if self._use_threads:
            # Wait for display to finish updating
            while self._event.is_set():
                time.sleep(1.0 / 10000)
            self._buffer = buffer
            self._event.set()
        else:
            self.write(buffer)

    def sync(self):
        while self._use_threads and self._event.is_set():
            pass

    def stop(self):
        self._running = False
        if self._use_threads and self._thread is not None:
            self._thread.join()
        self.write(numpy.zeros((self.w, self.h, self.BYTES_PER_PIXEL), dtype=numpy.uint8).tobytes())

    def __del__(self):
        self.stop()


class Multiverse:
    def __init__(self, *args):
        self.displays = list(args)

    def setup(self, use_threads=True):
        for display in self.displays:
            display.setup(use_threads)

        # Get any user signal handlers
        self._delegate_handler = signal.getsignal(signal.SIGINT)
        # Install our own
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        self.stop()
        if callable(self._delegate_handler):
            self._delegate_handler(sig, frame)

    def stop(self):
        for display in self.displays:
            display.stop()

    def add(self, display):
        self.displays.append(display)

    def bootloader(self):
        for display in self.displays:
            display.bootloader()

    def reset(self):
        for display in self.displays:
            display.reset()

    def update(self, buffer):
        for display in self.displays:
            display.update(buffer)

    def play_note(self, *args, **kwargs):
        for display in self.displays:
            display.play_note(*args, **kwargs)

