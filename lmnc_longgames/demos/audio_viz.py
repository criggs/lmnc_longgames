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

class numpy_data_buffer:
    """
    A fast, circular FIFO buffer in numpy with minimal memory interactions by using an array of index pointers
    """

    def __init__(self, n_windows, samples_per_window, dtype = numpy.float32, start_value = 0, data_dimensions = 1):
        self.n_windows = n_windows
        self.data_dimensions = data_dimensions
        self.samples_per_window = samples_per_window
        self.data = start_value * numpy.ones((self.n_windows, self.samples_per_window), dtype = dtype)

        if self.data_dimensions == 1:
            self.total_samples = self.n_windows * self.samples_per_window
        else:
            self.total_samples = self.n_windows

        self.elements_in_buffer = 0
        self.overwrite_index = 0

        self.indices = numpy.arange(self.n_windows, dtype=numpy.int32)
        self.last_window_id = numpy.max(self.indices)
        self.index_order = numpy.argsort(self.indices)

    def append_data(self, data_window):
        self.data[self.overwrite_index, :] = data_window

        self.last_window_id += 1
        self.indices[self.overwrite_index] = self.last_window_id
        self.index_order = numpy.argsort(self.indices)

        self.overwrite_index += 1
        self.overwrite_index = self.overwrite_index % self.n_windows

        self.elements_in_buffer += 1
        self.elements_in_buffer = min(self.n_windows, self.elements_in_buffer)

    def get_most_recent(self, window_size):
        ordered_dataframe = self.data[self.index_order]
        if self.data_dimensions == 1:
            ordered_dataframe = numpy.hstack(ordered_dataframe)
        return ordered_dataframe[self.total_samples - window_size:]

    def get_buffer_data(self):
        return self.data[:self.elements_in_buffer]


class AudioVizDemo(MultiverseGame):


    def __init__(self, multiverse_displays):
        super().__init__("Audio Viz", 120, multiverse_displays, fixed_fps = True)

        self.bar_width = 3
        self.chunk_pow = 10
        self.bar_num = 20
        self.chunk = 2 ** self.chunk_pow

        self.fft_bins = [int(v) for v in numpy.logspace(0,self.chunk_pow - 1, num = self.bar_num + 3, base=2)[2:]]

        # WTF?
        self.update_window_n_frames = 132
        self.updates_per_second = 1000
        self.data_windows_to_buffer = int(self.updates_per_second / 2)
        self.data_buffer = numpy_data_buffer(self.data_windows_to_buffer, self.update_window_n_frames)



        self.s = 0

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

        
    def non_blocking_stream_read(self, in_data, frame_count, time_info, status):
        if self.data_buffer is not None:
            # self.data_buffer.append_data(numpy.frombuffer(in_data, dtype=numpy.int16))
            # self.new_data = True
            self.buffer = in_data
            self.s = 0

        return in_data, pyaudio.paContinue

    # def getFFT(self, data, log_scale=False):
    #     '''
    #     Borrowed from: https://github.com/aiXander/Realtime_PyAudio_FFT/blob/master/src/fft.py
    #     Author danielloera
    #     '''
        # data = data * numpy.hamming(len(data))
        # try:
        #     FFT = numpy.abs(numpy.fft.rfft(data)[1:])
        # except:
        #     FFT = numpy.fft.fft(data)
        #     left, right = numpy.split(numpy.abs(FFT), 2)
        #     FFT = numpy.add(left, right[::-1])

        # FFT = numpy.abs(numpy.fft.rfft(data)[1:])

        # if log_scale:
        #     try:
        #         FFT = numpy.multiply(20, numpy.log10(FFT))
        #     except Exception as e:
        #         print('Log(FFT) failed: %s' %str(e))

        # return FFT

    def loop(self, events: List, dt: float):

        for event in events:
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()

        start = time.time()
        self.screen.fill(BLACK)


        #buffer = self.data_buffer.get_most_recent(1)[0]
        if self.buffer is None:
            return
        # fft = self.getFFT(numpy.frombuffer(self.buffer, dtype=numpy.int16), False)
        
        #fft = numpy.abs(numpy.fft.rfft(numpy.frombuffer(self.buffer, dtype=numpy.int16))[1:])
        
        data = numpy.fft.rfft(numpy.frombuffer(self.buffer, dtype=numpy.int16))[1:]
        fft = numpy.sqrt(numpy.real(data)**2+numpy.imag(data)**2) / self.chunk 

        # Use a pretty green for our histogram
        color = (0, 128, 128)
        #self.max_val = max(self.max_val, max(fft))

        scale_value = self.height / self.max_val
        # for index and value in the frequencies
        # for i,v in enumerate(fft):
        #     scaled_value = int(v * scale_value)
        #     start = (i * self.upscale_factor * self.bar_width, self.height * self.upscale_factor)
        #     end = (i * self.upscale_factor * self.bar_width, (self.height - scaled_value) * self.upscale_factor)
        #     pygame.draw.line(self.screen, color, start, end, width = self.upscale_factor * self.bar_width)

        for i in range(self.bar_num):
            #v = fft[self.fft_bins[i]]
            v = numpy.mean(fft[self.fft_bins[i]:self.fft_bins[i+1]])
            scaled_value = int(v * scale_value)
            r = pygame.rect.Rect(i * self.bar_width * self.upscale_factor, 
                (self.height - scaled_value) * self.upscale_factor,
                self.bar_width * self.upscale_factor,
                scaled_value * self.upscale_factor)
            pygame.draw.rect(self.screen, color, r)


        rendered_text = font.render("Testing", False, (135, 0, 135))
        rendered_text = pygame.transform.scale_by(rendered_text, self.upscale_factor)
        self.screen.blit(rendered_text, (0, 0))


                        

    def reset(self):
        self.setup_video()
