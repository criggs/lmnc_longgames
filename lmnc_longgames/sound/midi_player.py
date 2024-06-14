import mido
import threading
import logging

from lmnc_longgames.multiverse.multiverse_game import PygameMultiverseDisplay
from lmnc_longgames.util.music import midi_to_hz

WAVEFORM_NOISE = 128
WAVEFORM_SQUARE = 64
WAVEFORM_SAW = 32
WAVEFORM_TRIANGLE = 16
WAVEFORM_SINE = 8
WAVEFORM_WAVE = 1

PHASE_ATTACK = 0
PHASE_DECAY = 1
PHASE_SUSTAIN = 2
PHASE_RELEASE = 3
PHASE_OFF = 4

class MidiPlayer:

    def __init__(self, midi_file_path, multiverse_display: PygameMultiverseDisplay):
        self.midi_file_path = midi_file_path
        self.multiverse_display = multiverse_display
        self._thread = None
        self._stop_flag = threading.Event()
        self._channel = 0
        
        print(f"Created Midi Player for {self.midi_file_path}")
    
    def start(self):
        logging.info(f"Starting midi thread: {self.midi_file_path}")
        if self._thread is not None:
            raise Exception("Thread is already started")
        self._thread = threading.Thread(target=self.run, name=f'midi-{self.midi_file_path}')
        self._thread.start()

    def run(self):
        logging.debug(f"Running midi thread: {self.midi_file_path}")
        self.midi_player = mido.MidiFile(self.midi_file_path)
        for message in self.midi_player.play():
            if self._stop_flag.is_set():
                logging.info(f"midi thread stop flag set: {self.midi_file_path}")
                self.stop_notes()
                return
            if message.type == 'note_on':
                logging.info(f"Playing note: C{message.channel}:{message.note}")
                note_hz = midi_to_hz(message.note)

                if message.channel == 2:
                    #drum note
                    self.play_note(3, 40, waveform=WAVEFORM_SAW)
                elif message.channel == 1:
                    #bass note
                    self.play_note(2, note_hz, waveform=WAVEFORM_SQUARE)
                else:
                    self.play_note(self._channel, note_hz, waveform=WAVEFORM_SAW)
                    self._channel = (self._channel + 1) % 2

        logging.info(f"song thread complete: {self.midi_file_path}")

        # Play off notes (0 hertz)
        self.stop_notes()

    def stop_notes(self):
        self.multiverse_display.play_note(0, 0, waveform=64)
        self.multiverse_display.play_note(1, 0, waveform=64)
        self.multiverse_display.play_note(2, 0, waveform=64)
        self.multiverse_display.play_note(3, 0, waveform=64)

    def play_note(self, channel, frequency, waveform):
        self.multiverse_display.play_note(channel, frequency, waveform=waveform)

    def stop(self):
        logging.info(f"Stopping midi thread: {self.midi_file_path}")
        self._stop_flag.set()
        # We don't want to block on a join here, as the run loop will not exit until it looks
        # for the next note to play. So, we'll just trust it to do the right thing... what could
        # go wrong?
        self._thread = None
        self.midi_player = None
                
        