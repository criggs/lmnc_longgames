from typing import List
import sys, os
import time
import logging
import itertools
import pygame
import numpy
from math import sqrt
import imageio.v3 as iio
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame
from lmnc_longgames.sound.microphone import Microphone

script_path = os.path.realpath(os.path.dirname(__file__))
font = pygame.font.Font(f"{script_path}/../icl8x8u.bdf", 8)

RATE = 44100 # in Hz

class SpectrumAnalyzer(MultiverseGame):

    def __init__(self, multiverse_display):
        super().__init__("Spectrum", 180, multiverse_display, fixed_fps = True)

        #Sample Config
        self.chunk_pow = 10
        self.chunk = 2 ** self.chunk_pow

        self.bars_per_screen = 2
        
        # Floor to filter out some noise
        self.fft_level_floor = 15
        self.max_val = 200

        device = self.config.config.get("audio", {}).get("main", "default")
        self.microphone = Microphone(device)
        self.update_bars(self.bars_per_screen)

    def update_bars(self, bars_per_screen):
        # 12 - 1
        # 12/3 - 1
        # 12/4 - 1
        # 12 / 2 - 1
        logging.info(f"Setting bars per screen to {bars_per_screen}")
        
        self.bar_width = (12 // bars_per_screen) - 1
        self.bars_per_screen = bars_per_screen # bps * width + bps needs to equal 12
        self.bar_num = self.multiverse_display.display_num * self.bars_per_screen # 2 bands per screen

        # start at 1, we don't want ot use 0
        self.fft_bins = [int(v) for v in numpy.logspace(1,self.chunk_pow - 1, num = self.bar_num + 1, base=2)]
        self.ranges_to_interpolate = self.find_ranges_to_interpolate(self.fft_bins)
        
        logging.debug(f"fft_bins: {self.fft_bins}")
    
    def find_ranges_to_interpolate(self, bins):
        prev = 0
        count = 0
        start = 0
        ranges = []
        for i in range(self.bar_num):
            n = self.fft_bins[i]
            if n == prev:
                count = count + 1
            else:
                if count > 0:
                    ranges.append((start, i-1))
                prev = n
                count = 0
                start = i

        logging.debug(f"bins: {bins}")
        logging.debug(f"Ranges: {ranges}")
        return ranges

    def interpolate_ranges(self, data):
        for (a,b) in self.ranges_to_interpolate:
            b = b + 1
            new_data_slice = numpy.linspace(data[a], data[b], num=b-a + 1)
            data[a:b+1] = new_data_slice

    def loop(self, events: List, dt: float):

        self.buffer = self.microphone.read_audio_buffer(2)

        for event in events:
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()

            if event.type == ROTATED_CW or (event.type == pygame.KEYUP and event.key == pygame.K_RIGHT):
                self.update_bars((self.bars_per_screen % 4) + 1)

            if event.type == ROTATED_CCW or (event.type == pygame.KEYUP and event.key == pygame.K_LEFT):
                self.update_bars((self.bars_per_screen - 2) % 4 + 1)

        start = time.time()

        if self.buffer is None:
            return
        
        self.screen.fill(BLACK)
        
        data = numpy.fft.rfft(numpy.frombuffer(self.buffer, dtype=numpy.int16))[1:]
        fft = numpy.sqrt(numpy.real(data)**2+numpy.imag(data)**2) / self.chunk 

        fft = fft

        color = (200, 0, 0)

        #TODO: Smooth this
        self.max_val = max(200, max(fft))

        scale_value = self.height / self.max_val
        
        band_offset = 0
        band_data = []

        for i in range(self.bar_num):
            l = self.fft_bins[i]
            r = self.fft_bins[i+1]

            if l == r:
                v = fft[l]
            else:
                v = numpy.mean(fft[l:r])
            v = v if v > self.fft_level_floor else 0
            scaled_value = int(v * scale_value)
            band_data.append(scaled_value)

        self.interpolate_ranges(band_data)
        
        for i in range(self.bar_num):
            scaled_value = band_data[i]
            left = band_offset * self.upscale_factor
            band_offset += self.bar_width
            if i % self.bars_per_screen != self.bars_per_screen - 1:
                band_offset += 1 # add a pixel of separation
            top = (self.height - scaled_value) * self.upscale_factor
            width = self.bar_width * self.upscale_factor
            height = scaled_value * self.upscale_factor
            r = pygame.rect.Rect(left, top, width, height)
            pygame.draw.rect(self.screen, color, r)

        # rendered_text = font.render("Testing", False, (135, 0, 135))
        # rendered_text = pygame.transform.scale_by(rendered_text, self.upscale_factor)
        # self.screen.blit(rendered_text, (0, 0))

    def teardown(self):
        logging.info("Tearing down audio_viz")
        self.microphone.teardown()