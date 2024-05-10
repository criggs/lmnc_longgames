from pygame import USEREVENT

from lmnc_longgames.util.music import midi_to_hz

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Events
BUTTON_PRESSED = USEREVENT + 1
BUTTON_RELEASED = USEREVENT + 2
ROTATED_CW = USEREVENT + 3
ROTATED_CCW = USEREVENT + 4

# System
MAX_MENU_INACTIVE_TIME = 60
DEMO_SWITCH_TIME = 120

# Controllers
CONTROLS = 0
P1 = 1
P2 = 2

# Buttons
ROTARY_PUSH = 0
BUTTON_A = 1
BUTTON_B = 2

BUTTON_RESET = 30
BUTTON_MENU = 31

BUTTON_BOUNCE_TIME_SEC = 0.005

#GPIO
PIN_RESET_RELAY = 19
PIN_BUTTON_SCREEN_RESET = 16
PIN_BUTTON_MENU = 20
PIN_BUTTON_GAME_RESET = 21
PIN_SWITCH_MUTE = 26

PIN_P1_ROT_PUSH = 17
PIN_P1_DT = 27
PIN_P1_CLK = 22
PIN_P1_A=9
PIN_P1_B=10

PIN_P2_ROT_PUSH = 23
PIN_P2_DT = 24
PIN_P2_CLK = 25
PIN_P2_A=7
PIN_P2_B=8

PIN_TRIGGER_OUT = 12
TRIGGER_OUT_ON_TIME = 0.05

# Notes
NOTES = [midi_to_hz(i) for i in range(0, 8*12)]

_C_MINOR_POS = [0,2,3,5,7,8,10]
C_MINOR = []

_A_MINOR_POS = [9,11,0,2,4,5,7]
A_MINOR = []

_PENTATONIC_POS = [1,3,6,8,10]
PENTATONIC = []
for i, note in enumerate(NOTES):
    note_pos = i % 12
    if note_pos in _C_MINOR_POS:
        C_MINOR.append(note)
    if note_pos in _A_MINOR_POS:
        A_MINOR.append(note)
    if note_pos in _PENTATONIC_POS:
        PENTATONIC.append(note)

_YOUTH_8500_MIDI_NOTES = [57,57,57,57,59,55,55,55,53,55,59,60,60,59,60,60,59,60,62,64,65,64,62,60,59]
YOUTH_8500_NOTES = [midi_to_hz(midi_note) for midi_note in _YOUTH_8500_MIDI_NOTES]
