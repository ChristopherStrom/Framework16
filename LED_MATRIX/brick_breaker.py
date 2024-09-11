import glob
import serial
import time
import threading
import random  # Add the random module

FWK_MAGIC = [0x32, 0xAC]
WIDTH = 9
HEIGHT = 35
PADDLE_WIDTH = 5
BLOCK_ROWS = 15  # Number of rows of breakable blocks
TIMEOUT = 60 # Number of seconds without hitting a ball before restarting

# Global flag to stop the brick breaker thread
brick_breaker_running = False

def stop_brick_breaker():
    global brick_breaker_running
    brick_breaker_running = False

# Detect the serial port
def detect_serial_port():
    ports = glob.glob('/dev/ttyACM*')
    if len(ports) >= 2:
        return ports[1]
    elif ports:
        return ports[0]
    else:
        return None

# Send raw command to the LED matrix
def send_command_raw(serial_connection, command):
    try:
        serial_connection.write(bytes(command))
    except (IOError, OSError) as ex:
        print(f"Error sending command: {ex}")

# Set brightness level for the LED matrix
def set_brightness(serial_connection, brightness_level):
    command = FWK_MAGIC + [0x00, brightness_level]
    send_command_raw(serial_connection, command)

# Function to flash the ball in the middle of the screen
def flash_ball_in_middle(serial_connection):
    for _ in range(3):  # Flash three times
        full_grid = [[0] * WIDTH for _ in range(HEIGHT)]
        full_grid[HEIGHT // 2][WIDTH // 2] = 1
        flattened_vals = [val for row in full_grid for val in row]
        vals = [0x00 for _ in range(40)]
        for i in range(len(flattened_vals)):
            if flattened_vals[i]:
                vals[i // 8] |= (1 << (i % 8))
        command = FWK_MAGIC + [0x06] + vals[:40]
        send_command_raw(serial_connection, command)
        time.sleep(0.3)  # Ball visible
        clear_leds(serial_connection)
        time.sleep(0.3)  # Ball invisible

# Clears the entire LED matrix by sending an empty grid
def clear_leds(serial_connection):
    full_grid = [[0] * WIDTH for _ in range(HEIGHT)]
    vals = [0x00 for _ in range(40)]
    command = FWK_MAGIC + [0x06] + vals
    send_command_raw(serial_connection, command)

# Brick Breaker game loop with bouncing and block-breaking mechanics
def brick_breaker_animation(serial_connection):
    global brick_breaker_running
    brick_breaker_running = True  # Set to True when the game starts

    def reset_game():
        """Resets ball, paddle, and blocks for a new game round."""
        return 4, HEIGHT - 4, 1, -1, (WIDTH - PADDLE_WIDTH) // 2, [[1] * WIDTH for _ in range(BLOCK_ROWS)]

    def ball_hit():
        """Resets the timer whenever the ball hits something."""
        nonlocal last_hit_time
        last_hit_time = time.time()

    # Initialize game variables
    ball_x, ball_y, ball_dx, ball_dy, paddle_x, blocks = reset_game()
    last_hit_time = time.time()  # Track the last time the ball hit something

    while brick_breaker_running:
        current_time = time.time()
        if current_time - last_hit_time > TIMEOUT:  # If time passed without a hit, reset the game
            flash_ball_in_middle(serial_connection)  # Optional: flash to indicate reset
            ball_x, ball_y, ball_dx, ball_dy, paddle_x, blocks = reset_game()
            ball_hit()  # Reset the timer after restarting the game

        full_grid = [[0] * WIDTH for _ in range(HEIGHT)]
        full_grid[0] = [1] * WIDTH  # Top line

        for i in range(PADDLE_WIDTH):
            full_grid[HEIGHT - 2][paddle_x + i] = 1  # Paddle

        full_grid[ball_y][ball_x] = 1

        # Draw blocks
        for row in range(BLOCK_ROWS):
            for col in range(WIDTH):
                if blocks[row][col] == 1:
                    full_grid[row + 1][col] = 1

        # Send the grid data to the matrix
        flattened_vals = [val for row in full_grid for val in row]
        vals = [0x00 for _ in range(40)]
        for i in range(len(flattened_vals)):
            if flattened_vals[i]:
                vals[i // 8] |= (1 << (i % 8))
        command = FWK_MAGIC + [0x06] + vals[:40]
        send_command_raw(serial_connection, command)

        # Update ball position
        ball_x += ball_dx
        ball_y += ball_dy

        # Ball hits left or right wall
        if ball_x < 0:
            ball_x = 0
            ball_dx = -ball_dx  # Reverse horizontal direction if going out of bounds
        elif ball_x >= WIDTH:
            ball_x = WIDTH - 1
            ball_dx = -ball_dx  # Reverse horizontal direction if going out of bounds

        # Ball hits the top wall
        if ball_y < 0:
            ball_y = 0
            ball_dy = -ball_dy  # Reverse vertical direction

        # Ball hits the bottom paddle
        elif ball_y == HEIGHT - 3 and paddle_x <= ball_x < paddle_x + PADDLE_WIDTH:
            ball_dy = -ball_dy  # Bounce the ball off the paddle
            ball_hit()  # Reset the hit timer when ball hits paddle
            
            # Shift the ball left or right 0 to 3 places randomly, ensuring it stays in bounds
            shift = random.randint(-3, 3)
            new_ball_x = ball_x + shift
            if new_ball_x < 0:
                ball_x = 0
            elif new_ball_x >= WIDTH:
                ball_x = WIDTH - 1
            else:
                ball_x = new_ball_x

            # Randomly switch between diagonal or straight bounce (1 out of 5 for straight)
            if random.choices([True, False], [1, 4])[0]:
                ball_dx = 0  # Straight vertical bounce (1 out of 5 chance)
            else:
                ball_dx = random.choice([-1, 1])  # Diagonal bounce (4 out of 5 chance)

        # Ball hits blocks
        if 1 <= ball_y < BLOCK_ROWS + 1:  # Ensure ball_y is within block row range
            if blocks[ball_y - 1][ball_x] == 1:  # Check for block collision
                blocks[ball_y - 1][ball_x] = 0  # Remove the block
                ball_dy = -ball_dy  # Reverse ball direction
                ball_hit()  # Reset the hit timer when ball hits a block

        # Ball goes past the paddle (missed)
        if ball_y >= HEIGHT - 2:
            flash_ball_in_middle(serial_connection)  # Flash the ball in the middle
            ball_x, ball_y, ball_dx, ball_dy, paddle_x, blocks = reset_game()  # Reset the game
            ball_hit()  # Reset the timer after game reset


        # Ball goes past the paddle (missed)
        if ball_y >= HEIGHT - 2:
            flash_ball_in_middle(serial_connection)  # Flash the ball in the middle
            ball_x, ball_y, ball_dx, ball_dy, paddle_x, blocks = reset_game()  # Reset the game
            ball_hit()  # Reset the timer after game reset

        # Move paddle to follow the ball
        if ball_dx == 1 and paddle_x + PADDLE_WIDTH < WIDTH:
            paddle_x += 1
        elif ball_dx == -1 and paddle_x > 0:
            paddle_x -= 1

        time.sleep(0.1)

    clear_leds(serial_connection)

# Start the animation in a separate thread
def start_brick_breaker_thread(serial_connection):
    breaker_thread = threading.Thread(target=brick_breaker_animation, args=(serial_connection,), daemon=True)
    breaker_thread.start()

# Main loop to detect the serial port and start the animation
def main_loop():
    SERIAL_PORT = detect_serial_port()
    if not SERIAL_PORT:
        return

    try:
        with serial.Serial(SERIAL_PORT, 115200) as ser:
            set_brightness(ser, 64)
            start_brick_breaker_thread(ser)
            
            while True:
                # Keep the main loop alive
                time.sleep(1)

    except (IOError, OSError) as ex:
        print(f"Error: {ex}")

if __name__ == "__main__":
    main_loop()
