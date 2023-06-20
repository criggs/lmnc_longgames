from typing import List
import pygame
import cv2
import numpy
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame

"""

"""


class VideoDemo(MultiverseGame):

    FIT_ALL = 0
    FIT_WIDTH = 1
    FIT_HEIGHT = 2

    def __init__(self, multiverse_displays, video_file_path, fit_mode = 0):
        self.video_file_path = video_file_path
        print(f'Playing video {video_file_path}')
        self.video = cv2.VideoCapture(video_file_path)

        fps = self.video.get(cv2.CAP_PROP_FPS)

        super().__init__("Video", fps, multiverse_displays)

        self.v_width = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.v_height = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)

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
        


    def loop(self, events: List, dt: float):
        
        self.screen.fill(BLACK)

        success, video_image = self.video.read()

        if success:
            video_surf = pygame.image.frombuffer(video_image.tobytes(), video_image.shape[1::-1], "BGR")
            video_surf = pygame.transform.scale(video_surf, (self.scaled_v_width, self.scaled_v_height))

            #Center the frame
            coords = ((self.width - self.scaled_v_width) // 2, (self.height - self.scaled_v_height) // 2)
            self.screen.blit(video_surf, coords)
        else:
            #TODO add option to stop, instead of loop
            # Restart the video
            self.video = cv2.VideoCapture(self.video_file_path)
            

    def reset(self):
        pass
