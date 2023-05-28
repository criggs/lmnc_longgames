#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Installing udev rules for /dev/serial/by-id/* paths"
UDEV_RULES_DIR=/usr/lib/udev/rules.d
sudo cp $DIR/files/60-serial.rules $UDEV_RULES_DIR/60-serial.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
