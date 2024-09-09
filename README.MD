# LED Matrix Control for Battery and Volume Indicator

This project controls an LED matrix (9x34) connected to `/dev/ttyACM0` and displays battery and volume indicators. The script reads the system's battery level and volume level, then uses the LED matrix to represent both statuses visually, with spacers between the sections. Additionally, it includes dynamic behavior for charging and updates the brightness.

## Features

- **Battery Indicator**: Displays the battery status with a dynamic row to show the current charge level.
- **Volume Indicator**: A zigzag pattern across two rows represents the current system volume.
- **Spacers**: Separators between icons for better clarity.
- **System Calls**: Uses system calls to fetch real-time battery and volume levels.
- **Brightness Control**: Adjusts brightness to 25% for better display visibility.

## Requirements

- **Python 3.x**
- **PySerial** library: Install with `pip install pyserial`
- A connected 9x34 LED matrix controlled through `/dev/ttyACM0`.

## How it Works

1. **Battery Indicator**:
    - The battery icon has a dynamic second row that adjusts based on the battery level. The more the battery is charged, the more LEDs light up on this row.
2. **Volume Indicator**:
    - The volume indicator displays a zigzag pattern, representing the current system volume across two rows. The pattern's length grows or shrinks depending on the volume percentage.
3. **Spacers**:
    - Blank and full rows separate the battery and volume icons for a clearer display.
4. **Brightness**:
    - The brightness is set to 25% to make the display easier to read.

## Installation

1. Clone this repository to your local machine.
2. Install required Python packages using:
    ```bash
    pip install pyserial
    ```
3. Run the script:
    ```bash
    python3 led_matrix.py
    ```

## System Requirements

- The script expects access to the system's battery and volume information through the following:
    - **Battery**: `/sys/class/power_supply/BAT1/capacity` and `/sys/class/power_supply/BAT1/status`.
    - **Volume**: Obtained using the `amixer` command to fetch the current system volume level.

## Script Structure

- `FWK_MAGIC`: The command sequence used for communication with the LED matrix controller.
- `SERIAL_PORT`: The device path of the LED matrix controller (`/dev/ttyACM0`).
- `set_brightness`: Adjusts the brightness of the entire LED matrix.
- `display_battery_icon`: Generates the battery icon based on the battery percentage.
- `display_volume_icon`: Generates the volume zigzag icon based on the system volume level.
- `combine_icons`: Combines the battery, volume, and spacer rows into a single array.
- `get_battery_level`: Retrieves the current battery level.
- `get_system_volume`: Retrieves the current system volume.
- `main_loop`: Continuously updates the LED matrix with the latest battery and volume levels.

## Example Display

