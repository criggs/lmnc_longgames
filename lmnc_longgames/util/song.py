from lmnc_longgames.constants import *

def get_next_note(pos, notes):
    pos = pos % len(notes)
    return notes[pos]