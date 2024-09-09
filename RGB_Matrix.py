import time
import serial

FWK_MAGIC = [0x32, 0xAC]
SERIAL_PORT = '/dev/ttyACM0'  # Assuming we use ACM0 for the LED controller

# Constants for the color values
COLORS = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'white': (255, 255, 255)
}

# Initialize the number of LEDs in your matrix
NUM_LEDS = 9 * 34  # Adjust to 9x34 or however many LEDs you have

def send_command_raw(serial_connection, command):
    try:
        serial_connection.write(command)
    except (IOError, OSError) as ex:
        print(f"Error sending command: {ex}")

def set_rgb_all(serial_connection, r, g, b):
    """Set all LEDs to the same RGB value."""
    vals = []
    
    # Loop over each LED and set the RGB values for each one
    for led in range(NUM_LEDS):
        vals += [r, g, b]
    
    # Send the RGB values to the matrix
    command = FWK_MAGIC + [0x06] + vals[:NUM_LEDS * 3]  # 0x06 is the command to set LED values
    send_command_raw(serial_connection, command)

def cycle_colors(serial_connection):
    """Cycle through red, green, blue, and white across all LEDs."""
    while True:
        for color, (r, g, b) in COLORS.items():
            print(f"Setting color: {color}")
            set_rgb_all(serial_connection, r, g, b)
            time.sleep(2)  # Display each color for 2 seconds

def main():
    try:
        with serial.Serial(SERIAL_PORT, 115200) as ser:
            cycle_colors(ser)  # This will now loop indefinitely
    except (IOError, OSError) as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    main()
