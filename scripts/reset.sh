#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$PYTHONPATH:$DIR/..

python3 $DIR/../lmnc_longgames/util/screen_power_reset.py