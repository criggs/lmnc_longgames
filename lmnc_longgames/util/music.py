def get_next_note(pos, notes):
    pos = pos % len(notes)
    return notes[pos]

def midi_to_hz(note):
    return round(2 ** ((note - 69) / 12) * 440)