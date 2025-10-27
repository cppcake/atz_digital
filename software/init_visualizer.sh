#!/bin/sh

sleep 10

# This section has been generated using GitHub CoPilot with GPT-4.1
export DISPLAY=:0
export XAUTHORITY=/home/cake/.Xauthority

chromium  --kiosk --start-fullscreen --incognito --no-memcheck  http://localhost/visualizer
