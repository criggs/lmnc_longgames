# lmnc_longgames

> **Warning**
> This is still under development. The code is messy, the comments are wrong, the documentation is lacking. Enter at your own risk, there be dragons 🐉

## Goal

20ish unicorn boards plugged into 3 usb hubs plugged into a raspberry pi

all to run pong :D

YouTube: https://www.youtube.com/watch?v=cm83RIhDbwo

## How does it work?

The 220 by 53 pixel display is made up of 20 Pimoroni Galactic Unicorns. Each one is controlled with a built-in Raspberry Pi Pico microcontroller running a custom firmware that displays whatever pixels it's sent over USB. The Unicorn displays are all connected to a Raspberry Pi 4 through a few USB hubs. The Raspberry Pi runs all of the game software, written in Python. It reads the player's controller input over GPIO and renders each full 220 by 53 pixel frame on the Pi as a 2d matrix of RGB values. As each full frame is rendered, it is split into 20 sub matrices, one for each Unicorn display. This data is sent to each Unicorn over the USB serial connection, where the custom Pico firmware takes the RGB pixel data and updates each of its LEDs. This happens anywhere from 60 times a second to 120 times a second. Because we're able to display any frame we want, we're not just limited to games. We can also send it video frames, or even frames from a webcam.

## Installation

Dependencies can be installed by running:

`scripts/install.sh`

## Configure your Screens

`scripts/setup_config.sh`

## Running Long Pong

`scripts/game.sh`

or

`scripts/game_headless.sh`

## Development

TODO

## Credits

Special Thanks goes to:
* Chris Riggs (VKTx/criggs)
* Dax
* Gadgetoid
* FineQuasar17
* TheEPROM9 LaTeX
* LMNC
* This Museum Is (Not) Obsolete
* Pimoroni
* LMNC Patreon Supporters
* 24 sausage and egg baguettees


## Relevant Links

* https://github.com/Gadgetoid/gu-multiverse
* https://shop.pimoroni.com/products/space-unicorns?variant=40842033561683

