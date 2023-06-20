from typing import List
import pygame
import cv2
import numpy
from lmnc_longgames.constants import *
from lmnc_longgames.multiverse.multiverse_game import MultiverseGame

"""

"""


class VideoDemo(MultiverseGame):
    def __init__(self, multiverse_displays):

        self.video = cv2.VideoCapture("/home/pi/Touhou - Bad Apple.mp4")
        #self.video = cv2.VideoCapture("/home/pi/Desktop/videoplayback.mp4")
        fps = self.video.get(cv2.CAP_PROP_FPS)

        super().__init__("Video", fps, multiverse_displays)

        self.v_width = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.v_height = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.scaled_v_width = int(self.v_width * (self.height / self.v_height))
        


    def loop(self, events: List, dt: float):
        
        self.screen.fill(BLACK)

        success, video_image = self.video.read()

        if success:
            video_surf = pygame.image.frombuffer(video_image.tobytes(), video_image.shape[1::-1], "BGR")
            #TODO Scale

            video_surf = pygame.transform.scale(video_surf, (self.scaled_v_width, self.height))

            # if self.upscale_factor != 1:
            #     # Upsample the sim to the windowed display
            #     buf = numpy.repeat(buf, self.upscale_factor, axis=1).repeat(
            #         self.upscale_factor, axis=0
            #     )
            self.screen.blit(video_surf, (0,0))

    def reset(self):
        pass
