# This file has been generated using GitHub CoPilot with GPT-4.1

import serial
import requests
import time

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200
URL_TEMPLATE = 'http://localhost:80/therapy/vote/{}/{}'

ANSWER_MAP = {
    "0": "green",
    "1": "yellow",
    "2": "red",
    "3": "blue",
    "4": "purple",
}

def open_serial_with_retry():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
            return ser
        except serial.SerialException as e:
            print(f"Failed to open serial port: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def process_line(line, session):
    parts = line.split(',')
    if len(parts) != 2:
        print(f"Malformed line: {line}")
        return

    id_str, answer_code = parts
    answer_str = ANSWER_MAP.get(answer_code)

    if answer_str:
        url = URL_TEMPLATE.format(id_str, answer_str)
        try:
            response = session.put(url)
            print(f"Sent to {url}, status: {response.status_code}")
        except requests.RequestException as e:
            print(f"HTTP request failed: {e}")
    else:
        print(f"Unknown answer code: {answer_code}")

def main():
    session = requests.Session()

    while True:
        with open_serial_with_retry() as ser:
            try:
                while True:
                    raw_line = ser.readline()
                    if not raw_line:
                        continue
                    try:
                        line = raw_line.decode('utf-8').strip()
                        if line:
                            process_line(line, session)
                    except UnicodeDecodeError as e:
                        print(f"Failed to decode line: {raw_line} ({e})")
            except (serial.SerialException, OSError) as e:
                print(f"Serial connection lost: {e}. Reconnecting...")
                time.sleep(1)

if __name__ == '__main__':
    main()
