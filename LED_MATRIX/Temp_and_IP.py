import glob
import serial
import time
import requests
import socket
from numbers import NUMBERS
from letters import LETTERS

FWK_MAGIC = [0x32, 0xAC]
WIDTH = 9
HEIGHT = 35

# Degree symbol represented as a 2-column wide grid
DEGREE = [
    [0, 1],
    [0, 0],
    [0, 0],
    [0, 0],
    [0, 0]
]

# Coordinates for the location
latitude = 30.06
longitude = -85.56

# NWS API endpoint to get forecast based on latitude and longitude
NWS_POINTS_API = f"https://api.weather.gov/points/{latitude},{longitude}"

def detect_serial_port():
    """Detect available /dev/ttyACM* ports and select the second one if available."""
    ports = glob.glob('/dev/ttyACM*')
    print(f"Detected serial ports: {ports}")
    if len(ports) >= 2:
        return ports[1]  # Return the second available port
    elif ports:
        return ports[0]  # If only one exists, return it
    else:
        print("No /dev/ttyACM* device found.")
        return None

def send_command_raw(serial_connection, command):
    """Send raw command to the serial connection."""
    try:
        serial_connection.write(bytes(command))
        print(f"Sent command: {command}")
    except (IOError, OSError) as ex:
        print(f"Error sending command: {ex}")

def set_brightness(serial_connection, brightness_level):
    """Set the brightness of the LED matrix."""
    command = FWK_MAGIC + [0x00, brightness_level]  # 0x00 is CommandVals.Brightness
    send_command_raw(serial_connection, command)

def get_nws_forecast_url():
    """Fetch forecast URL and gridpoint information using latitude and longitude."""
    try:
        response = requests.get(NWS_POINTS_API)
        data = response.json()
        forecast_url = data['properties']['forecastHourly']  # Use forecastHourly for hourly temperature
        return forecast_url
    except Exception as e:
        print(f"Error fetching forecast URL: {e}")
        return None

def get_current_temperature_and_icon_from_forecast(forecast_url):
    """Fetch the current temperature and weather icon from the hourly forecast API."""
    try:
        response = requests.get(forecast_url)
        forecast_data = response.json()

        # Get the first period (current hour) from the hourly forecast
        current_period = forecast_data['properties']['periods'][0]
        current_temp = current_period['temperature']
        short_forecast = current_period['shortForecast']

        print(f"Current Hour Temperature: {current_temp}°F, Forecast: {short_forecast}")
        return current_temp, short_forecast
    except Exception as e:
        print(f"Error fetching temperature and icon: {e}")
        return None, None

def get_forecast_text(short_forecast):
    """Map shortForecast keywords to corresponding forecast words."""
    short_forecast = short_forecast.lower()

    if "cloud" in short_forecast:
        return 'Cloudy'
    elif "sun" in short_forecast or "clear" in short_forecast:
        return 'Sunny'
    elif "rain" in short_forecast or "showers" in short_forecast:
        return 'Rain'
    elif "snow" in short_forecast:
        return 'Snow'
    elif "thunderstorm" in short_forecast or "storm" in short_forecast:
        return 'Storm'
    elif "wind" in short_forecast:
        return 'Windy'
    elif "fog" in short_forecast:
        return 'Fog'
    elif "haze" in short_forecast:
        return 'Hazy'
    else:
        return 'N/A'  # Default to 'N/A' if no match

def get_private_ip():
    """Get the private IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "N/A"

def get_public_ip():
    """Get the public IP address."""
    try:
        response = requests.get('https://api.ipify.org', params={'format': 'text'})
        return response.text
    except Exception:
        return "N/A"

def scroll_text(text):
    """Convert text into a grid of 5 rows for scrolling."""
    text_grid = []

    # Prepare the grid for the text with smooth scrolling
    for row in range(5):  # 5 rows for letters
        row_data = []
        for char in text:
            if char == ".":
                row_data += NUMBERS["DOT"][row]  # Use DOT for IP addresses
            else:
                row_data += LETTERS[char.upper()][row] if char.isalpha() else NUMBERS[char][row]  # Use letters/numbers
            row_data.append(0)  # Add a space between characters
        row_data += [0, 0, 0, 0, 0]  # Add three extra spaces for smooth scrolling (plus the usual two spaces)
        text_grid.append(row_data)
    return text_grid

import time

def display_temperature_and_scroll(serial_connection, temperature, forecast_word, private_ip, public_ip):
    """Display the current temperature statically and scroll the forecast, private, and public IPs."""
    print(f"Displaying temperature: {temperature}°F with forecast: {forecast_word}")

    # Convert the temperature to string and split into digits
    temp_str = str(temperature)

    # Prepare the grid for the temperature display
    temperature_grid = []
    for row in range(5):  # 5 rows for digits
        row_data = []
        for i, digit in enumerate(temp_str):
            row_data += NUMBERS[digit][row]  # Add the digit representation
            if i < len(temp_str) - 1:  # Add 1-column spacer between digits, but not after the last digit
                row_data.append(0)
        row_data += DEGREE[row]  # Add the degree icon
        temperature_grid.append(row_data)

    # Prepare scrolling text grids
    forecast_grid = scroll_text(forecast_word)
    private_ip_grid = scroll_text(private_ip)
    public_ip_grid = scroll_text(public_ip)

    # Initialize offsets for scrolling
    forecast_offset = 0
    private_ip_offset = 0
    public_ip_offset = 0

    # Get the lengths of the grids for scrolling
    forecast_length = len(forecast_grid[0])
    private_ip_length = len(private_ip_grid[0])
    public_ip_length = len(public_ip_grid[0])

    while True:
        full_grid = [[0] * WIDTH for _ in range(35)]  # 9x35 grid for the whole display

        # Scroll the forecast (rows 0–4)
        for row in range(5):
            visible_part = forecast_grid[row][forecast_offset:forecast_offset + WIDTH]
            if len(visible_part) < WIDTH:
                visible_part += forecast_grid[row][:WIDTH - len(visible_part)]
            full_grid[row][:WIDTH] = visible_part

        # Display the static temperature (rows 6–10)
        for row in range(5):
            full_grid[6 + row][:WIDTH] = temperature_grid[row][:WIDTH]

        # Scroll the private IP (rows 17–24)
        for row in range(5):
            visible_part = private_ip_grid[row][private_ip_offset:private_ip_offset + WIDTH]
            if len(visible_part) < WIDTH:
                visible_part += private_ip_grid[row][:WIDTH - len(visible_part)]
            full_grid[17 + row][:WIDTH] = visible_part

        # Scroll the public IP (rows 29–34)
        for row in range(5):
            visible_part = public_ip_grid[row][public_ip_offset:public_ip_offset + WIDTH]
            if len(visible_part) < WIDTH:
                visible_part += public_ip_grid[row][:WIDTH - len(visible_part)]
            full_grid[29 + row][:WIDTH] = visible_part

        # Flatten the grid into a 1D array
        flattened_vals = [val for row in full_grid for val in row]

        # Prepare the `vals` array (39 bytes for 35 rows by 9 columns = 315 bits)
        vals = [0x00 for _ in range(39)]
        for i in range(min(len(flattened_vals), 315)):  # 315 bits for 35x9 grid
            if flattened_vals[i]:
                vals[i // 8] |= (1 << (i % 8))  # Convert bits to bytes

        # Send FWK_MAGIC + command identifier + packed data
        command = FWK_MAGIC + [0x06] + vals
        send_command_raw(serial_connection, command)

        # Update scroll offsets and wrap around when reaching the end
        forecast_offset = (forecast_offset + 1) % forecast_length
        private_ip_offset = (private_ip_offset + 1) % private_ip_length
        public_ip_offset = (public_ip_offset + 1) % public_ip_length

        # Adjust the scroll speed
        time.sleep(0.2)  # Adjust the scroll speed if necessary

def main_loop():
    global SERIAL_PORT
    SERIAL_PORT = detect_serial_port()
    if not SERIAL_PORT:
        print("No serial port found. Exiting...")
        return

    last_weather_check = 0
    last_ip_check = 0
    weather_interval = 600  # 10 minutes in seconds
    ip_interval = 60  # 1 minute in seconds

    forecast_word = None
    private_ip = None
    public_ip = None

    try:
        with serial.Serial(SERIAL_PORT, 115200) as ser:
            set_brightness(ser, 64)  # Set brightness to 25%

            while True:
                current_time = time.time()

                # Check weather every 10 minutes
                if current_time - last_weather_check >= weather_interval:
                    forecast_url = get_nws_forecast_url()
                    if forecast_url:
                        temperature, short_forecast = get_current_temperature_and_icon_from_forecast(forecast_url)
                        if temperature:
                            forecast_word = get_forecast_text(short_forecast)
                        else:
                            print("Failed to fetch temperature and forecast.")
                    last_weather_check = current_time

                # Check IPs every 1 minute
                if current_time - last_ip_check >= ip_interval:
                    private_ip = get_private_ip()
                    public_ip = get_public_ip()
                    last_ip_check = current_time

                # Ensure values are not None before displaying
                if forecast_word and private_ip and public_ip:
                    display_temperature_and_scroll(ser, temperature, forecast_word, private_ip, public_ip)

                # Small delay before the next loop iteration
                time.sleep(1)

    except (IOError, OSError) as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    main_loop()
