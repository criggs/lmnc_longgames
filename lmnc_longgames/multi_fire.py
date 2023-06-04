import numpy
import time
import random
import threading, signal, sys
from multiverse import Multiverse, Display
from config import LongGameConfig


config = LongGameConfig()
displays = [Display(f'{file}', 53, 11, 0, 11 * i) for i, file in enumerate(config.config['displays']['main']['devices'] )]
display = Multiverse(*displays)

display.setup()
display.start()

# Full buffer size
WIDTH = 11 * len(displays)
HEIGHT = 53
BYTES_PER_PIXEL = 4

# Fire stuff
FIRE_SPAWNS = 4
DAMPING_FACTOR = 0.98
HEAT = 4.0

# Palette conversion, this is actually pretty nifty
PALETTE = numpy.array([
    [0, 0, 0, 0],
    [20, 20, 20, 0],
    [0, 30, 180, 0],
    [0, 160, 220, 0],
    [180, 255, 255, 0]
], dtype=numpy.uint8)

# FIIIREREEEEEEE
heat = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.float32)


# UPDATE THE FIIIIIIIIIIIIREEEEEEEEEEEEEEEEEEEEEEEEEE
def update():
    # Clear the bottom two rows (off screen)
    heat[HEIGHT - 1][:] = 0.0
    heat[HEIGHT - 2][:] = 0.0

    # Add random fire spawns
    for c in range(FIRE_SPAWNS):
        x = random.randint(0, WIDTH - 4) + 2
        heat[HEIGHT - 1][x - 1:x + 1] = HEAT / 2.0
        heat[HEIGHT - 2][x - 1:x + 1] = HEAT

    # Propagate the fire upwards
    a = numpy.roll(heat, -1, axis=0)  # y + 1, x
    b = numpy.roll(heat, -2, axis=0)  # y + 2, x
    c = numpy.roll(heat, -1, axis=0)  # y + 1
    d = numpy.roll(c, 1, axis=1)      # y + 1, x + 1
    e = numpy.roll(c, -1, axis=1)     # y + 1, x - 1

    # Average over 5 adjacent pixels and apply damping
    heat[:] += a + b + d + e
    heat[:] *= DAMPING_FACTOR / 5.0


# Framerate counters, don't mind these
sum_total = 0
num_frames = 0

event = threading.Event()

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    event.set()

signal.signal(signal.SIGINT, signal_handler)


while not event.wait(1/80):
    t_start = time.time()

    # Update the fire
    update()

    # Convert the fire buffer to RGB 888X (uint32 as four bytes)
    buf = heat.clip(0.0, 1.0) * 4
    buf = numpy.rot90(buf)
    buf = buf.astype(numpy.uint8)
    buf = PALETTE[buf]

    # Update the displays from the buffer
    display.update(buf)

    # Just FPS stuff, move along!
    t_end = time.time()
    t_total = t_end - t_start

    sum_total += t_total
    num_frames += 1

    if num_frames == 60:
        print(f"Took {sum_total:.04f}s for 60 frames, {num_frames / sum_total:.02f} FPS")
        num_frames = 0
        sum_total = 0

display.stop()
sys.exit(0)