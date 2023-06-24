from typing import List
import time
import logging
import itertools
import pygame
import imageio.v3 as iio
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame

'''
Play the video
'''
class VideoDemo(MultiverseGame):

    FIT_ALL = 0
    FIT_WIDTH = 1
    FIT_HEIGHT = 2

    def __init__(self, multiverse_displays, video_file_path, fit_mode = FIT_HEIGHT, tile = True):
        self.video_file_path = video_file_path
        print(f'Playing video {video_file_path}')

        super().__init__("Video", 60, multiverse_displays, fixed_fps = True)
        
        self.fit_mode = fit_mode
        self.tile = tile
        self.setup_video()

        self.v_height, self.v_width, _ = self.frame.shape
        
        screen_ratio = self.width / self.height
        video_ratio = self.v_width / self.v_height
        
        if fit_mode == self.FIT_ALL:
            if video_ratio > screen_ratio:
                #Video Wider that screen. Fit to width
                fit_mode = self.FIT_WIDTH
            else:
                #Video taller than screen. Fit to height
                fit_mode = self.FIT_HEIGHT

        if fit_mode == self.FIT_WIDTH:
            self.scaled_v_width = self.width
            self.scaled_v_height = int(self.width * (self.v_height / self.v_width))

        if fit_mode == self.FIT_HEIGHT:
            self.scaled_v_width = int(self.height * (self.v_width / self.v_height))
            self.scaled_v_height = self.height        

    def setup_video(self):
        raw_height = self.multiverse_display.height/self.multiverse_display.upscale_factor
        raw_width = self.multiverse_display.width/self.multiverse_display.upscale_factor

        if '<video' in self.video_file_path:
            self.fps = 30
            print(f"Resetting FPS to {self.fps} for video")
            self.frame_iter = iio.imiter(self.video_file_path, fps="30", size=(320,240))
        else:
            scale_param = f"-1:{raw_height}" if self.fit_mode == self.FIT_HEIGHT else f"{raw_width}:-1"
            self.frame_iter = iio.imiter(
                self.video_file_path,
                plugin="pyav",
                format="rgb24",
                filter_sequence=[("scale", f"{scale_param}:flags=neighbor"),("fps", f"{self.fps}")]
            )
        self.frame = next(self.frame_iter)

    def loop(self, events: List, dt: float):

        for event in events:
            if event.type == BUTTON_RELEASED and event.input in [BUTTON_A]:
                self.reset()

            if event.type == BUTTON_RELEASED and event.input in [BUTTON_B, ROTARY_PUSH]:
                self.exit_game()

        start = time.time()
        self.screen.fill(BLACK)

        video_surf = pygame.image.frombuffer(self.frame.tobytes(), self.frame.shape[1::-1], "RGB")
        video_surf = pygame.transform.scale(video_surf, (self.scaled_v_width, self.scaled_v_height))

        #Center the frame
        coords = ((self.width - self.scaled_v_width) // 2, (self.height - self.scaled_v_height) // 2)
        
        
        if self.tile:
            x_vals = itertools.chain(range(coords[0], 0-self.width, -self.scaled_v_width), range(coords[0], self.width, self.scaled_v_width))
            y_vals = itertools.chain(range(coords[1], 0-self.height, -self.scaled_v_height), range(coords[1], self.height, self.scaled_v_height))
            blit_coords = itertools.product(x_vals, y_vals)
            for tile_coords in blit_coords:
                self.screen.blit(video_surf, tile_coords)
        else:
            self.screen.blit(video_surf, coords)
        
        elapsed = time.time() - start

        if self.frame_count  % 100 == 0:
            logging.debug(f'Drawing frame took {elapsed * 1000} ms')
        
        try:

            start = time.time()
            self.frame = next(self.frame_iter)
            elapsed = time.time() - start

            if self.frame_count  % 100 == 0:
                logging.debug(f'Next video frame took {elapsed * 1000} ms')
        except StopIteration:
            self.setup_video()
                        

    def reset(self):
        self.setup_video()
