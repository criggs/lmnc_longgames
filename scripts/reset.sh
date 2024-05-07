#!/bin/bash
set -e

# DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# export PYTHONPATH=$PYTHONPATH:$DIR/..

# python3 $DIR/../lmnc_longgames/util/screen_power_reset.py

for f in /dev/serial/by-id/*; do
    echo "Resetting $f"
    echo -n "multiverse:_rst" > $f
    sleep 1
done