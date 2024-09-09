import psutil
import time
import serial
import os
import subprocess
import glob

FWK_MAGIC = [0x32, 0xAC]
SERIAL_PORT = None  # Placeholder for the serial port that will be detected
WIDTH = 9  # Number of columns
HEIGHT = 34  # Number of rows
CPU_HISTORY = [[0] * 10 for _ in range(9)]  # Initialize a 9x10 grid for CPU history
MEMORY_HISTORY = [[0] * 10 for _ in range(9)]  # Initialize a 9x10 grid for memory history

def detect_serial_port():
    """Detect the first available /dev/ttyACM* port."""
    ports = glob.glob('/dev/ttyACM*')
    if ports:
        return ports[0]  # Return the first available serial port
    else:
        print("No /dev/ttyACM* device found.")
        return None

def send_command_raw(serial_connection, command):
    try:
        serial_connection.write(command)
    except (IOError, OSError) as ex:
        print(f"Error sending command: {ex}")

def set_brightness(serial_connection, brightness_level):
    """Set the brightness of the LED matrix."""
    command = FWK_MAGIC + [0x00, brightness_level]  # 0x00 is CommandVals.Brightness
    send_command_raw(serial_connection, command)

def display_battery_icon(battery_percentage, combined_grid):
    """Display the battery icon with dynamic second row indicating charge level."""
    battery_icon = [
        [1, 1, 1, 1, 1, 1, 1, 1, 0],  # Row 1 (top)
        [1, 0, 0, 0, 0, 0, 0, 1, 1],  # Row 2 (dynamic row for battery level)
        [1, 1, 1, 1, 1, 1, 1, 1, 0],  # Row 3 (bottom)
    ]
    
    # Update row 2 based on battery percentage
    led_count = int(6 * (battery_percentage / 100))  # 6 LEDs to display charge level
    for i in range(1, led_count + 1):
        battery_icon[1][i] = 1

    # Insert the battery icon into the combined grid (assumed to be rows 0-2 in the combined grid)
    for row in range(3):
        combined_grid[row] = battery_icon[row]

    return combined_grid

def display_volume_icon(volume_percentage, combined_grid):
    """Display a zigzag pattern across 2 rows for volume level based on percentage."""
    volume_icon = [
        [0] * 9,  # Row 7 (top row for zigzag)
        [0] * 9,  # Row 8 (bottom row for zigzag)
    ]
    
    # Zigzag pattern scaling
    zigzag_length = int(9 * (volume_percentage / 100))  # Determine length of zigzag (max 9 columns)
    
    # Ensure alternating pattern for top and bottom rows
    for i in range(zigzag_length):
        if i % 2 == 0:
            volume_icon[1][i] = 1  # Set LED on bottom row first
        else:
            volume_icon[0][i] = 1  # Set LED on top row
    
    # Debug output to console
    print(f"Volume Level: {volume_percentage}%")
    print("Volume Icon (Top Row 7):", volume_icon[0])
    print("Volume Icon (Bottom Row 8):", volume_icon[1])
    
    # Insert the volume icon into the combined grid (assumed to be rows 7-8 in the combined grid)
    for row in range(2):
        combined_grid[6 + row] = volume_icon[row]
    
    return combined_grid

def map_percentage_to_rows(usage_percentage):
    """Map the usage percentage to the corresponding number of rows (out of 10)."""
    if usage_percentage <= 5:
        return 1
    elif usage_percentage <= 10:
        return 2
    elif usage_percentage <= 25:
        return 3
    elif usage_percentage <= 30:
        return 4
    elif usage_percentage <= 50:
        return 5
    elif usage_percentage <= 60:
        return 6
    elif usage_percentage <= 70:
        return 7
    elif usage_percentage <= 80:
        return 8
    elif usage_percentage <= 90:
        return 9
    else:  # 90-100%
        return 10

def shift_and_update_cpu_usage(cpu_usage):
    """Shift CPU usage history to the left and update with the latest usage."""
    global CPU_HISTORY

    # Shift the history left
    for i in range(8):
        CPU_HISTORY[i] = CPU_HISTORY[i + 1]

    # Map the current CPU usage to the correct number of rows based on the scale
    usage_rows = map_percentage_to_rows(cpu_usage)

    # Update the last column with the new CPU usage value (list of row values for the last column)
    CPU_HISTORY[8] = [1 if row < usage_rows else 0 for row in range(10)]

def shift_and_update_memory_usage(memory_usage):
    """Shift memory usage history to the left and update with the latest usage."""
    global MEMORY_HISTORY

    # Shift the history left
    for i in range(8):
        MEMORY_HISTORY[i] = MEMORY_HISTORY[i + 1]

    # Map the current memory usage to the correct number of rows based on the scale
    usage_rows = map_percentage_to_rows(memory_usage)

    # Update the last column with the new memory usage value (list of row values for the last column)
    MEMORY_HISTORY[8] = [1 if row < usage_rows else 0 for row in range(10)]

def display_usage_icon(usage_history, combined_grid, start_row):
    """Display CPU or memory usage history as bars on the matrix, starting from the bottom."""
    # Populate the grid based on usage history, starting from the bottom (row 9) and moving up
    for col in range(9):
        for row in range(10):
            combined_grid[start_row + (9 - row)][col] = usage_history[col][row]  # Update the combined grid

    return combined_grid

def add_spacer():
    """Create a spacer row."""
    return [
        [0] * 9,  # Blank spacer row
        [1] * 9,  # Full row for separation
        [0] * 9,  # Another blank spacer row
    ]
    
def add_blank_spacer():
    """Create a spacer row."""
    return [
        [0] * 9,  # Blank spacer row
        [0] * 9,  # Full row for separation
        [0] * 9,  # Another blank spacer row
    ]

def combine_icons(battery_icon, volume_icon, cpu_icon, memory_icon):
    """Combine all icons into a single display array."""
    combined = []
    combined.extend(battery_icon)
    combined.extend(add_spacer())  # Add spacer after battery
    combined.extend(volume_icon)
    combined.extend(add_spacer())  # Add spacer after volume
    combined.extend(cpu_icon)
    combined.extend(add_spacer())  # Add spacer after CPU
    combined.extend(memory_icon)
    return combined

def get_battery_level():
    """Retrieve the battery level from the system."""
    try:
        with open("/sys/class/power_supply/BAT1/capacity", "r") as f:
            battery_level = int(f.read().strip())
            return battery_level
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
    global SERIAL_PORT
    SERIAL_PORT = detect_serial_port()
    if not SERIAL_PORT:
        print("No serial port found. Exiting...")
        return

    try:
        with serial.Serial(SERIAL_PORT, 115200) as ser:
            set_brightness(ser, 64)  # Set brightness to 25%
            combined_grid = [[0] * 9 for _ in range(34)]  # Initialize a 9x34 grid for the full display

            while True:
                battery_level = get_battery_level()  # Get actual battery level
                volume_level = get_system_volume()  # Get actual volume level
                cpu_usage = psutil.cpu_percent()  # Get current CPU usage
                memory_usage = psutil.virtual_memory().percent  # Get current memory usage

                # Print for debugging
                print(f"Memory Usage: {memory_usage}%")
                print(f"CPU Usage: {cpu_usage}%")

                # Update CPU and memory usage histories and shift
                shift_and_update_cpu_usage(cpu_usage)
                shift_and_update_memory_usage(memory_usage)

                # Generate the icons and update the combined grid
                combined_grid = display_battery_icon(battery_level, combined_grid)

                # Add spacer after battery
                spacer = add_spacer()
                combined_grid[3:6] = spacer

                combined_grid = display_volume_icon(volume_level, combined_grid)

                # Add spacer after volume
                spacer = add_spacer()
                combined_grid[8:11] = spacer

                combined_grid = display_usage_icon(CPU_HISTORY, combined_grid, start_row=11)  # CPU icon at rows 11-20

                # Add spacer after CPU
                spacer = add_spacer()
                combined_grid[21:24] = spacer

                # Memory usage history
                combined_grid = display_usage_icon(MEMORY_HISTORY, combined_grid, start_row=24)  # Memory icon at rows 24-33

                # If charging, animate the battery charging
                if is_charging():
                    animate_battery_charge(ser, battery_level, combined_grid)
                else:
                    # Flatten the combined grid (34 rows by 9 columns = 306 bits)
                    flattened_vals = [val for row in combined_grid for val in row]
                    
                    # Prepare the `vals` array (39 bytes)
                    vals = [0x00 for _ in range(39)]
                    for i in range(min(len(flattened_vals), 306)):  # 306 bits for 34x9 grid
                        if flattened_vals[i]:
                            vals[i // 8] |= (1 << (i % 8))  # Convert to bytes

                    command = FWK_MAGIC + [0x06] + vals
                    send_command_raw(ser, command)

                time.sleep(1)  # Wait 1 second

    except (IOError, OSError) as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    main_loop()
