import time
import serial
import os
import subprocess

FWK_MAGIC = [0x32, 0xAC]
SERIAL_PORT = '/dev/ttyACM0'
WIDTH = 9  # Number of columns
HEIGHT = 34  # Number of rows

def send_command_raw(serial_connection, command):
    try:
        serial_connection.write(command)
    except (IOError, OSError) as ex:
        print(f"Error sending command: {ex}")

def set_brightness(serial_connection, brightness_level):
    """Set the brightness of the LED matrix."""
    command = FWK_MAGIC + [0x00, brightness_level]  # 0x00 is CommandVals.Brightness
    send_command_raw(serial_connection, command)

def display_battery_icon(battery_percentage):
    """Display the battery icon with dynamic second row indicating charge level."""
    battery_icon = [
        [1, 1, 1, 1, 1, 1, 1, 1, 0],  # Row 1 (top)
        [1, 0, 0, 0, 0, 0, 0, 1, 1],  # Row 2 (dynamic row)
        [1, 1, 1, 1, 1, 1, 1, 1, 0],  # Row 3 (bottom)
    ]
    
    # Update row 2 based on battery percentage
    led_count = int(6 * (battery_percentage / 100))  # 6 LEDs to display charge level
    for i in range(1, led_count + 1):
        battery_icon[1][i] = 1

    return battery_icon

def display_volume_icon(volume_percentage):
    """Display a zigzag pattern across 2 rows for volume level based on percentage."""
    volume_icon = [
        [0] * 9,  # Row 7 (top row for zigzag)
        [0] * 9,  # Row 8 (bottom row for zigzag)
    ]
    
    # Zigzag pattern scaling
    zigzag_length = int(9 * (volume_percentage / 100))  # Determine length of zigzag
    for i in range(zigzag_length):
        if i % 2 == 0:
            volume_icon[1][i] = 1  # Bottom row of zigzag
        else:
            volume_icon[0][i] = 1  # Top row of zigzag
    
    return volume_icon

def add_spacer():
    """Create a spacer row."""
    return [
        [0] * 9,  # Blank spacer row
        [1] * 9,  # Full row for separation
        [0] * 9,  # Another blank spacer row
    ]

def combine_icons(battery_icon, volume_icon):
    """Combine the battery icon, spacer, and volume icon into a single display array."""
    combined = []
    combined.extend(battery_icon)
    combined.extend(add_spacer())  # Add spacer after battery
    combined.extend(volume_icon)
    combined.extend(add_spacer())  # Add spacer after volume
    return combined

def get_battery_level():
    """Retrieve the battery level from the system."""
    try:
        with open("/sys/class/power_supply/BAT1/capacity", "r") as f:
            battery_level = int(f.read().strip())
            return battery_level
            
            #Debug Battery
            #print(f"Current Battery Level: {battery_level}%")
    except FileNotFoundError:
        print("Could not find battery capacity file.")
        return 0

def is_charging():
    """Check if the laptop is charging."""
    try:
        with open("/sys/class/power_supply/BAT1/status", "r") as f:
            status = f.read().strip()
            return status == "Charging"
    except FileNotFoundError:
        print("Could not find battery status file.")
        return False

def get_system_volume():
    """Retrieve the current system volume level."""
    try:
        result = subprocess.run(['amixer', 'get', 'Master'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        
        # Find the volume percentage for 'Front Left' or 'Front Right'
        for line in output.split('\n'):
            if 'Front Left:' in line or 'Front Right:' in line:
                volume = int(line.split('[')[1].split('%')[0])  # Extract volume percentage
                return volume
    except Exception as e:
        print(f"Error retrieving system volume: {e}")
        return 0

def main_loop():
    """Main loop to display battery status and handle animations."""
    try:
        with serial.Serial(SERIAL_PORT, 115200) as ser:
            set_brightness(ser, 64)  # Set brightness to 25%

            while True:
                battery_level = get_battery_level()  # Get actual battery level
                volume_level = get_system_volume()  # Get actual volume level

				#Debug Volume level
                #print(f"Current Volume Level: {volume_level}%")

                # Generate the icons
                battery_icon = display_battery_icon(battery_level)
                volume_icon = display_volume_icon(volume_level)

                # Combine the icons with spacers
                combined_vals = combine_icons(battery_icon, volume_icon)
                
                # Flatten the combined array into a single row format for LED matrix
                vals = [0x00 for _ in range(39)]  # Initialize 9x34 LED grid
                flattened_vals = [val for row in combined_vals for val in row]  # Flatten the icon
                
                for i in range(len(flattened_vals)):
                    if flattened_vals[i]:
                        vals[i // 8] |= (1 << (i % 8))  # Turn on the LED
                
                command = FWK_MAGIC + [0x06] + vals  # 0x06 is CommandVals.Draw
                send_command_raw(ser, command)

                time.sleep(1)  # Show for 1 second
                
                if is_charging():
                    # Charging animation logic can go here
                    pass
                else:
                    time.sleep(5)  # Wait 5 seconds before the next update

    except (IOError, OSError) as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    main_loop()
