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
import sounddevice as sd

from lmnc_longgames.sound.microphone import Microphone

script_path = os.path.realpath(os.path.dirname(__file__))
font = pygame.font.Font(f"{script_path}/../icl8x8u.bdf", 8)

RATE = 44100 # in Hz

GAIN_STEP = 0.5
GAIN_MAX = 10
GAIN_MIN = 0.5

DECAY_COLOR = (0, 30, 75)
BACKGROUND_DECAY = 0.0075

class Waveform(MultiverseGame):

    def __init__(self, multiverse_display):
        super().__init__("Waveform", 180, multiverse_display, fixed_fps = True)

        self.gain = 2.0

        device = self.config.config.get("audio", {}).get("main", "default")

        try:
            self.microphone = Microphone(device)
        except Exception as e:
            logging.error(f"Failed to initialize microphone: {e}")
            self.microphone = None

        self.background = None
        

    def scale_samples_to_surf(self, width, height, samples):
        """ Returns a generator containing (x, y) to draw a waveform.

        :param width: width of surface to scale points to.
        :param height: height of surface to scale points to.
        :param samples: an array of signed 1 byte or signed 2 byte.
        """
        # precalculate a bunch of variables, so not done in the loop.
        len_samples = len(samples)
        width_per_sample = width / len_samples
        height_1 = height - 1

        factor = 1.0 / 65532
        normalize_modifier = int(65532 / 2)

        return ((
            int((sample_number + 1) * width_per_sample),
            int(
                (1.0 -
                    (factor *
                        (samples[sample_number] + normalize_modifier)))
                * (height_1)
            ))
        for sample_number in range(len_samples))

    def draw_wave(self, surf,
                samples,
                wave_color = (0, 0, 0),
                background_color = pygame.Color('white')):
        """Draw array of sound samples as waveform into the 'surf'.

        :param surf: Surface we want to draw the wave form onto.
        :param samples: an array of signed 1 byte or signed 2 byte.
        :param wave_color: color to draw the wave form.
        :param background_color: to fill the 'surf' with.
        """
        if background_color is not None:
            surf.fill(background_color)
        width, height = surf.get_size()
        points = tuple(self.scale_samples_to_surf(width, height, samples))
        pygame.draw.lines(surf, wave_color, False, points, width=self.upscale_factor)



    def loop(self, events: List, dt: float):

        if self.microphone is None:
            self.exit_game()
        else:
            self.buffer = self.microphone.read_audio_buffer()

        for event in events:
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()

            if event.type == ROTATED_CW or (event.type == pygame.KEYUP and event.key == pygame.K_RIGHT):
                self.gain = min(self.gain + GAIN_STEP, GAIN_MAX)

            if event.type == ROTATED_CCW or (event.type == pygame.KEYUP and event.key == pygame.K_LEFT):
                self.gain = max(self.gain - GAIN_STEP, GAIN_MIN)


        start = time.time()

        if self.buffer is None:
            return
        
        # We don't want to clear the screen if we didn't get a new buffer
        self.screen.fill(BLACK)
        
        values = self.buffer * self.gain

        # Don't think this actually does anything. Need to calculate the largest scaler and clamp that based on initial values
        # # Clamp if clipping
        # max_val = numpy.max(numpy.abs(values))
        # if(max_val > 32767):
        #     values = values * (32767/max_val)

        # Here we should how to draw it onto a screen.
        wf = pygame.Surface((self.width, self.height)).convert_alpha()
        self.draw_wave(wf, values, wave_color=(255,0,0), background_color=(0,0,0,0))
        self.screen.fill(BLACK)

        wave_frame = pygame.surfarray.array3d(wf)

        np_wave_frame = numpy.array(wave_frame)

        #replace red in the np_wave_frame with the color we want
        np_wave_frame[np_wave_frame[:,:,0] == 255] = DECAY_COLOR

        if self.background is None:
            self.background = np_wave_frame
        else:

            scaledDecay = BACKGROUND_DECAY * (self.fps * dt)
            # half the values in the background
            self.background = self.background * (1 - scaledDecay)
            # update background to have matching pixels from np_wave_frame
            self.background = numpy.where(np_wave_frame == DECAY_COLOR, np_wave_frame, self.background)
        

        background_frame = pygame.surfarray.map_array(self.screen, numpy.round(self.background).astype(int))
        pygame.surfarray.blit_array(self.screen, background_frame)
        
        self.screen.blit(wf, (0, 0))

    def teardown(self):
        self.microphone.teardown()