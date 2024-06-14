import logging
import numpy
import sounddevice as sd

def initialize_sd():
    # We need to reinitialize sounddevice to make sure we can get the full list of devices
    sd._terminate()
    sd._initialize()
    print(sd.query_devices())


class Microphone:

    def __init__(self, microphone_name="default", microphone_index=0):
        self.microphone_name = microphone_name
        self.microphone_index = int(microphone_index)
        self.chunk = 1024
        self.setup_audio()

    def setup_audio(self):
        self.buffer = None

        candidate_devices = sorted([d for d in sd.query_devices() if self.microphone_name in d['name']], key=lambda d: d['name'])

        if len(candidate_devices) < self.microphone_index + 1:
            raise Exception(f"No microphones found with name {self.microphone_name} with index {self.microphone_index}")

        device = candidate_devices[self.microphone_index]

        logging.info(f"Found main mic: {device}")

        self.stream = sd.InputStream(
            channels=1,
            device=device.get("index"),
            samplerate=int(device.get("default_samplerate")), 
            blocksize=self.chunk,
            dtype='int16')
        

    # Reads a buffer of audio from the microphone. Will block until the requesteed number of chunks has been read.
    # Returns a numpy array of int16 values
    def read_audio_buffer(self, number_of_chunks=1):
        if not self.stream.active:
            #start the stream the on the first read
            self.stream.start()
            return None
        
        readSize = self.chunk * number_of_chunks
        buffer = None
    
        while buffer is None or buffer.size < readSize:
            framesToRead = self.stream.read_available
            framesToRead = (framesToRead//self.chunk)*self.chunk
            if framesToRead >= self.chunk:
                newBuffer, _ = self.stream.read(framesToRead)
                # The buffer is an array of arrays for each channel
                # We only want the first channel, so we need to flatten it
                # We also don't care about every sample, so truncate
                if buffer is None:
                    buffer = newBuffer[:,0]
                else:
                    buffer = numpy.append(buffer, newBuffer[:,0])
        
        return buffer[:readSize]
    
    def teardown(self):
        logging.info("Tearing down microphone")
        try:
            self.stream.close()
            self.stream = None
        except Exception as e:
            logging.error("Exception while stopping stream.", exc_info=e)

def main():
    print(sd.query_devices())

if __name__ == "__main__":
    main()