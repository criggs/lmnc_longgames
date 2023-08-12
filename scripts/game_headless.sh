#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#We need to set XDG_RUNTIME_DIR for pulseaudio to be available while running through systemd
export XDG_RUNTIME_DIR=/run/user/$(id -u $USER)
export PYTHONPATH=$PYTHONPATH:$DIR/..

python3 $DIR/../lmnc_longgames/multiverse/multiverse_game.py "$@"
