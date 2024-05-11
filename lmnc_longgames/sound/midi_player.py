import mido
import threading
import logging

from lmnc_longgames.multiverse.multiverse_game import PygameMultiverseDisplay
from lmnc_longgames.util.music import midi_to_hz


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
                return
            if message.type == 'note_on':
                logging.info(f"Playing note: {message.note}")
                note_hz = midi_to_hz(message.note)
                self.multiverse_display.play_note(self._channel, note_hz, release=1000, waveform=32)
                self._channel = (self._channel + 1) % 4
        logging.info(f"song thread complete: {self.midi_file_path}")

    def stop(self):
        logging.info(f"Stopping midi thread: {self.midi_file_path}")
        self._stop_flag.set()
        # We don't want to block on a join here, as the run loop will not exit until it looks
        # for the next note to play. So, we'll just trust it to do the right thing... what could
        # go wrong?
        self._thread = None
        self.midi_player = None
                
        