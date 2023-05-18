# lmnc_longpong

## Goal

20ish unicorn boards plugged into 3 usb hubs pluged into a raspberry pi

all to run pong :D

## Installation

Make sure you have python 3 installed

Make sure the following python libraries are installed:
* pygame
* piserial
* RPi.GPIO

## Running Long Pong

`python3 lmnc_longgames/longpong.py -w`

### Arguments
```
-h                 Help
-c <CONFIG>        Configruation File
-w                 Show Pygame Window  
```

## Development

Install Poetry for dependency management: https://python-poetry.org/docs/#installation

Add a new dependency with `poetry add <dependency>`

Build a release with `poetry build`. Releases will be in the `dist` directory.

## Relevant Links

* https://github.com/Gadgetoid/gu-multiverse
* https://github.com/Daft-Freak/32blit-beta/blob/multiverse/32blit-sdl/UnicornMultiverse.cpp
* https://www.pygame.org/docs/ref/bufferproxy.html