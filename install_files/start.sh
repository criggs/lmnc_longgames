#!/bin/bash -l

echo "Starting service"


echo "rebinding usb"
sudo /home/pi/rebind.sh

echo "Sleeping to stabalize"
sleep 10

echo "Launching longpong"
cd /home/pi
/home/pi/projects/lmnc_longgames/scripts/game_headless.sh

echo "Service stopped"
