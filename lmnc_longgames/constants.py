from pygame import USEREVENT

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

#GPIO
PIN_RESET_RELAY = 19
PIN_MENU_BUTTON = 20
PIN_GAME_RESET = 21
PIN_MUTE_SWITCH = 26

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

NOTES = []
for i in range(1,9):
    for note in [16.35, 17.32, 18.35, 19.45, 20.60, 21.83, 23.12, 24.50, 25.96, 27.50, 29.14, 30.87]:
        NOTES.append(round(note * i))

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


