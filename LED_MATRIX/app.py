import threading
import time
import serial
from settings import DELAY, WIDTH, HEIGHT, BRIGHTNESS
from led_serial import FWK_MAGIC, detect_serial_port, set_brightness, clear_leds, send_command_raw
from weather import get_nws_forecast_url, get_current_temperature_and_icon_from_forecast, get_forecast_text
from ipaddresses import get_private_ip, get_public_ip
from generation import scroll_text, generate_temperature_grid, combine_grids
from brick_breaker import start_brick_breaker_thread, clear_leds, stop_brick_breaker
from system_monitor import main_loop as system_monitor_loop  # Import the main loop of system_monitor.py

shared_data = {
    "temperature": None,
    "forecast_word": None,
    "private_ip": None,
    "public_ip": None
}
data_lock = threading.Lock()

# Flag to track the state of the IP availability
no_public_ip = False 

def display_temperature_and_scroll(serial_connection):
    forecast_offset = 0
    private_ip_offset = 0
    public_ip_offset = 0

    while True:
        with data_lock:
            temperature = shared_data["temperature"]
            forecast_word = shared_data["forecast_word"]
            private_ip = shared_data["private_ip"]
            public_ip = shared_data["public_ip"]

        # If no public IP, stop the normal display loop
        if no_public_ip:
            time.sleep(1)  # Pause while brick breaker runs
            continue

        if temperature is None or forecast_word is None or private_ip is None or public_ip is None:
            time.sleep(1)
            continue

        # Generate grids for each part of the display
        forecast_grid = scroll_text(forecast_word)
        temperature_grid = generate_temperature_grid(temperature)
        private_ip_grid = scroll_text(private_ip)
        public_ip_grid = scroll_text(public_ip)

        forecast_length = len(forecast_grid[0])
        private_ip_length = len(private_ip_grid[0])
        public_ip_length = len(public_ip_grid[0])

        # Apply the offsets for scrolling
        visible_forecast = [row[forecast_offset:forecast_offset + WIDTH] for row in forecast_grid]
        visible_private_ip = [row[private_ip_offset:private_ip_offset + WIDTH] for row in private_ip_grid]
        visible_public_ip = [row[public_ip_offset:public_ip_offset + WIDTH] for row in public_ip_grid]

        # Wrap the text if the offset exceeds the length of the grid
        for row in range(5):
            if len(visible_forecast[row]) < WIDTH:
                visible_forecast[row] += forecast_grid[row][:WIDTH - len(visible_forecast[row])]
            if len(visible_private_ip[row]) < WIDTH:
                visible_private_ip[row] += private_ip_grid[row][:WIDTH - len(visible_private_ip[row])]
            if len(visible_public_ip[row]) < WIDTH:
                visible_public_ip[row] += public_ip_grid[row][:WIDTH - len(visible_public_ip[row])]

        # Combine grids for the final display
        full_grid = [[0] * WIDTH for _ in range(35)]
        for row in range(5):
            full_grid[row][:WIDTH] = visible_forecast[row]
        for row in range(5):
            full_grid[6 + row][:WIDTH] = temperature_grid[row][:WIDTH]
        for row in range(5):
            full_grid[17 + row][:WIDTH] = visible_private_ip[row]
        for row in range(5):
            full_grid[29 + row][:WIDTH] = visible_public_ip[row]

        # Flatten the grid for the LED matrix and send it
        flattened_vals = [val for row in full_grid for val in row]
        vals = [0x00 for _ in range(39)]
        for i in range(min(len(flattened_vals), 315)):
            if flattened_vals[i]:
                vals[i // 8] |= (1 << (i % 8))

        command = FWK_MAGIC + [0x06] + vals
        send_command_raw(serial_connection, command)
        set_brightness(serial_connection, BRIGHTNESS)

        # Update the scrolling offsets
        forecast_offset = (forecast_offset + 1) % forecast_length
        private_ip_offset = (private_ip_offset + 1) % private_ip_length
        public_ip_offset = (public_ip_offset + 1) % public_ip_length

        time.sleep(DELAY)

def update_data(serial_connection):
    global no_public_ip
    last_weather_check = 0
    last_ip_check = 0
    weather_interval = 600
    ip_interval = 5

    try:
        while True:
            current_time = time.time()

            if current_time - last_weather_check >= weather_interval:
                forecast_url = get_nws_forecast_url()
                if forecast_url:
                    temp, short_forecast = get_current_temperature_and_icon_from_forecast(forecast_url)
                    with data_lock:
                        if temp is not None:
                            shared_data["temperature"] = temp
                            shared_data["forecast_word"] = get_forecast_text(short_forecast)
                        else:
                            shared_data["temperature"] = " "
                            shared_data["forecast_word"] = " "
                last_weather_check = current_time

            if current_time - last_ip_check >= ip_interval:
                private_ip = get_private_ip()
                public_ip = get_public_ip()
                with data_lock:
                    shared_data["private_ip"] = private_ip
                    shared_data["public_ip"] = public_ip

                # Check if public IP is available
                if public_ip == " ":
                    if not no_public_ip:
                        clear_leds(serial_connection)
                        start_brick_breaker_thread(serial_connection)
                    no_public_ip = True
                else:
                    if no_public_ip:
                        stop_brick_breaker()  # Stop the brick breaker
                        clear_leds(serial_connection)  # Clear the screen before resuming normal display
                    no_public_ip = False

                last_ip_check = current_time

            time.sleep(1)

    except Exception as e:
        print(f"Error in update_data thread: {e}")

def start_threads(serial_connection):
    display_thread = threading.Thread(target=display_temperature_and_scroll, args=(serial_connection,), daemon=True)
    display_thread.start()

    # Start the thread to handle the system monitoring (CPU, memory, battery, etc.)
    system_monitor_thread = threading.Thread(target=system_monitor_loop, daemon=True)
    system_monitor_thread.start()

    data_thread = threading.Thread(target=update_data, args=(serial_connection,), daemon=True)
    data_thread.start()

def main_loop():
    SERIAL_PORT = detect_serial_port()
    if not SERIAL_PORT:
        print("No serial port detected.")
        return

    try:
        with serial.Serial(SERIAL_PORT, 115200) as ser:
        
            start_threads(ser)
            while True:
                time.sleep(1)

    except (IOError, OSError) as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    main_loop()
