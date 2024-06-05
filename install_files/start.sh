#!/bin/bash -l

echo "Starting service"

# Get the current time in seconds since epoch
current_time=$(date +%s)

# Get the last reboot time of the system in seconds since epoch
last_reboot=$(date -d "$(uptime -s)" +%s)

# Calculate the time difference in seconds
time_diff=$((current_time - last_reboot))

# Check if the server has been rebooted in the last 60 seconds
if [ "$time_diff" -le 60 ]; then
    echo "Rebooted recently. Sleeping for 30 seconds."
    sleep 30
fi

echo "rebinding usb"
sudo /home/pi/rebind.sh

echo "Sleeping to stabalize"
sleep 10

echo "Launching longpong"
cd /home/pi
/home/pi/projects/lmnc_longgames/scripts/game_headless.sh

echo "Service stopped"
