#!/bin/bash

DEVICES="1-0 1-1 1-2 2-0 2-1 2-2 3-0 3-1 3-2 4-0 4-1 4-1 5-0 5-1 5-2 6-0 6-1 6-2"


for device in $DEVICES; do
    echo "Rebinding $device"
    echo "$device:1.0" | tee /sys/bus/usb/drivers/hub/unbind
    echo "$device:1.0"| tee /sys/bus/usb/drivers/hub/bind
done
