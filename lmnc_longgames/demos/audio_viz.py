from typing import List
import sys, os
import time
import logging
import itertools
import pygame
import pyaudio
import numpy
from math import sqrt
import imageio.v3 as iio
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame

script_path = os.path.realpath(os.path.dirname(__file__))
font = pygame.font.Font(f"{script_path}/../icl8x8u.bdf", 8)

RATE = 44100 # in Hz

class AudioVizDemo(MultiverseGame):

    def __init__(self, multiverse_display):
        super().__init__("Audio Viz", 120, multiverse_display, fixed_fps = True)

        #Sample Config
        self.chunk_pow = 10
        self.chunk = 2 ** self.chunk_pow

        self.setup_audio()


    def setup_audio(self):
        self.update_bars(1)

        self.buffer = None

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = pyaudio.paInt16,
            channels = 1,
            rate = RATE,
            input=True,
            output=False,
            frames_per_buffer=self.chunk,
            stream_callback=self.non_blocking_stream_read
        )
        self.max_val = 200

        print(self.chunk)
        print(self.chunk_pow)
        print(self.bar_num)
        print(self.fft_bins)

    def update_bars(self, bars_per_screen):
        # 12 - 1
        # 12/3 - 1
        # 12/4 - 1
        # 12 / 2 - 1
        logging.info(f"Setting bars per screen to {bars_per_screen}")
        
        self.bar_width = (12 // bars_per_screen) - 1
        self.bars_per_screen = bars_per_screen # bps * width + bps needs to equal 12
        self.bar_num = self.multiverse_display.display_num * self.bars_per_screen # 2 bands per screen
        self.fft_bins = [int(v) for v in numpy.logspace(0,self.chunk_pow - 1, num = self.bar_num + 3, base=2)[2:]]
        
    def non_blocking_stream_read(self, in_data, frame_count, time_info, status):
        self.buffer = in_data
        return in_data, pyaudio.paContinue


    def loop(self, events: List, dt: float):

        for event in events:
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()

        start = time.time()
        self.screen.fill(BLACK)

        if self.buffer is None:
            return
        
        data = numpy.fft.rfft(numpy.frombuffer(self.buffer, dtype=numpy.int16))[1:]
        fft = numpy.sqrt(numpy.real(data)**2+numpy.imag(data)**2) / self.chunk 

        color = (200, 0, 0)
        #self.max_val = max(self.max_val, max(fft))

        scale_value = self.height / self.max_val
        
        band_offset = 0
        for i in range(self.bar_num):
            #v = fft[self.fft_bins[i]]

            l = self.fft_bins[i]
            r = self.fft_bins[i+1]
            if r >= l:
                # TODO Change this to an average between the previous and next bins, unless it's the first
                r = l + 1
            v = numpy.mean(fft[l:r])
            scaled_value = int(v * scale_value)

            left = band_offset * self.upscale_factor
            band_offset += self.bar_width
            if i % self.bars_per_screen != self.bars_per_screen - 1:
                band_offset += 1 # add a pixel of separation
            top = (self.height - scaled_value) * self.upscale_factor
            width = self.bar_width * self.upscale_factor
            height = scaled_value * self.upscale_factor
            r = pygame.rect.Rect(left, top, width, height)
            pygame.draw.rect(self.screen, color, r)


        rendered_text = font.render("Testing", False, (135, 0, 135))
        rendered_text = pygame.transform.scale_by(rendered_text, self.upscale_factor)
        self.screen.blit(rendered_text, (0, 0))

        if self.frame_count % 120 == 0:
            self.update_bars(((self.bars_per_screen) % 4 ) + 1)


                        

    def reset(self):
        self.setup_audio()

    def teardown(self):
        logging.info("Tearing down audio_viz")
        try:
            self.stream.close()
        except Exception as e:
            logging.error("Exception while stopping pyaudio stream.", exc_info=e)