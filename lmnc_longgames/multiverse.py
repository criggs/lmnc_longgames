"""
Copyright 2021 (c)

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
   disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import numpy
import serial
import threading
import time
import traceback


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
        self.display_buffer = None
        self.exit_flag = threading.Event()
        self.is_setup = False
    
    def update(self, buffer):
        #threading.Thread(target=self.write, args=(buffer,)).start()
        self.display_buffer = buffer

    def run(self):
        print(f"{self.x},{self.y}: Running....")
        while not self.exit_flag.wait(timeout=0.01):
            if not self.is_setup:
                self.setup()
            self.write(self.display_buffer)
        
        print(f"{self.x},{self.y}: Running loop has finished")
        self.clear()
        self._close()
        print(f"{self.x},{self.y}: Run is done")

    def stop(self):
        print(f"{self.x},{self.y}: Stopping display thread")
        self.exit_flag.set()

    def join(self):
        print(f"{self.x},{self.y}: Waiting for thread to stop")
        self.thread.join()

    def start(self) -> threading.Thread:
        print(f"{self.x},{self.y}: Starting display thread")
        self.exit_flag.clear()
        self.thread = threading.Thread(target = self.run)
        self.thread.start()
        return self.thread
    
    def setup(self):
        try:
            self.port = serial.Serial(self.path, write_timeout=1)
            self.clear()
            self.is_setup = True
        except Exception as e:
            print(f"{self.x},{self.y}: Exception while setting up display")
            print(e)
            
    def write(self, buffer):
        if buffer is not None:
            self._write(buffer[self.y:self.y + self.h, self.x:self.x + self.w].tobytes())

    def _write(self, display_buffer):
        if display_buffer is None or self.port is None or not self.port.isOpen():
            return
        try:
            self.port.write(display_buffer)
        except Exception as e:
            print(f"{self.x},{self.y}: Error while writing")
            print(e)
            traceback.print_exc()

    def clear(self):
        print(f"{self.x},{self.y}: Clearing display")
        self._write(numpy.zeros((self.w, self.h, self.BYTES_PER_PIXEL), dtype=numpy.uint8).tobytes())

    def _close(self):
        print(f"{self.x},{self.y}: Cleaning up and Closing port")
        print(f"{self.x},{self.y}: Resetting input buffer")
        self.port.reset_input_buffer()
        print(f"{self.x},{self.y}: Resetting output buffer")
        self.port.reset_output_buffer()
        print(f"{self.x},{self.y}: Closing port")
        self.port.close()
        self.port = None
        self.is_setup = False

    def __del__(self):
        if self.port is None or not self.port.isOpen():
            return
        try:
            print(f"{self.x},{self.y}: __del__ cleaning up display")
            self.exit_flag.set()
            self._close()
        except:
            pass



class Multiverse:
    def __init__(self, *args):
        self.displays = list(args)
        self.exit_flag = threading.Event()

    def add(self, display):
        self.displays.append(display)

    def update(self, buffer):
        for display in self.displays:
            display.update(buffer)

    def stop(self):
        print("Stopping multiverse displays")
        for d in self.displays:
            d.stop()
        print("Waiting for display threads to stop")
        for d in self.displays:
            d.join()
        print("Multiverse display stop complete")

    def start(self) -> threading.Thread:
        print("Starting multiverse displays")
        for d in self.displays:
            d.start()
        print("Multiverse display start complete")
 