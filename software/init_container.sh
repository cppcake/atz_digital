#!/usr/bin/env bash

set -e

cd ./app

# Start the FastAPI Server in background
python3 -m uvicorn main:app --log-level critical --host 0.0.0.0 --port 80 &

# Start the serial listener in background
python3 ../serial_listener.py &

wait
