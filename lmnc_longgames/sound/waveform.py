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

class Waveform(MultiverseGame):

    def __init__(self, multiverse_display):
        super().__init__("Waveform", 60, multiverse_display, fixed_fps = True)

        #Sample Config
        self.chunk_pow = 10
        self.chunk = 2 ** self.chunk_pow

        self.setup_audio()


    def setup_audio(self):
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

    def non_blocking_stream_read(self, in_data, frame_count, time_info, status):
        self.buffer = in_data
        return in_data, pyaudio.paContinue


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

        for event in events:
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()

        start = time.time()
        self.screen.fill(BLACK)

        if self.buffer is None:
            return

        values = numpy.frombuffer(self.buffer, dtype=numpy.int16)

        # Here we should how to draw it onto a screen.
        wf = pygame.Surface((self.width, self.height)).convert_alpha()
        self.draw_wave(wf, values, wave_color=(255,0,0), background_color=BLACK)
        self.screen.fill(BLACK)
        self.screen.blit(wf, (0, 0))

        
    def reset(self):
        self.setup_audio()

    def teardown(self):
        logging.info("Tearing down audio_viz")
        try:
            self.stream.close()
        except Exception as e:
            logging.error("Exception while stopping pyaudio stream.", exc_info=e)