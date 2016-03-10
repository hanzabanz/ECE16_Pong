__author__ = 'hannah'

WAVFILE = 'sounds/BallBounce.wav'
# import pygame
# from pygame import *
# import sys
#
# mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
# pygame.init()
# print pygame.mixer.get_init(),
# screen=pygame.display.set_mode((400,400),32)
#
# while True:
#     for event in pygame.event.get():
#         if event.type == QUIT:
#             pygame.quit()
#             sys.exit()
#         if event.type == KEYDOWN:
#             if event.key==K_ESCAPE:
#                  pygame.quit()
#                  sys.exit()
#             elif event.key==K_UP:
#                 s = pygame.mixer.Sound(WAVFILE)
#                 ch = s.play()
#                 # while ch.get_busy():
#                 #     pygame.time.delay(100)
#                 time.sleep(2)
#     pygame.display.update()

# import time, sys
# from pygame import mixer
#
# # pygame.init()
# mixer.init()
#
# sound = mixer.Sound(WAVFILE)
# sound.play()
# mixer.pause()
# time.sleep(2)
# mixer.unpause()


import pygame
from pygame import *
import sys

mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
pygame.init()
screen=pygame.display.set_mode((400,400),32)
# pygame.mixer.music.load(WAVFILE)
# pygame.mixer.music.play(-1, 0.0)

sound = pygame.mixer.Sound("sounds/BallBounce.wav")

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key==K_ESCAPE:
                 pygame.quit()
                 sys.exit()
            elif event.key==K_UP:
                # pygame.mixer.music.play(-1, 0.0)
                pass
            elif event.key==K_DOWN:
                # pygame.mixer.music.stop()
                sound.play()
                pygame.time.delay(1500)
    pygame.display.update()
