# led-serial.py
import glob
import serial
import time
from settings import DEBUG

FWK_MAGIC = [0x32, 0xAC]
WIDTH = 9
HEIGHT = 35
DEGREE = [
    [0, 1],
    [0, 0],
    [0, 0],
    [0, 0],
    [0, 0]
]

def detect_serial_port():
    ports = glob.glob('/dev/ttyACM*')
    if len(ports) >= 2:
        return ports[1]
    elif ports:
        return ports[0]
    else:
        if DEBUG:
            print("No serial ports found.")
        return None

def send_command_raw(serial_connection, command):
    try:
        serial_connection.write(bytes(command))
    except (IOError, OSError) as ex:
        print(f"Error sending command: {ex}")

def set_brightness(serial_connection, brightness_level):
    command = FWK_MAGIC + [0x00, brightness_level]
    send_command_raw(serial_connection, command)

def clear_leds(serial_connection):
    full_grid = [[0] * WIDTH for _ in range(35)]
    flattened_vals = [val for row in full_grid for val in row]
    vals = [0x00 for _ in range(39)]
    command = FWK_MAGIC + [0x06] + vals
    send_command_raw(serial_connection, command)
