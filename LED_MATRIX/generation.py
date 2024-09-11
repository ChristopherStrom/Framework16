# generation.py
from dictionary import DICTIONARY
from settings import WIDTH, HEIGHT

def scroll_text(text):
    text_grid = []
    for row in range(5):
        row_data = []
        for char in text:
            if char == ".":
                row_data += DICTIONARY["DOT"][row]
            else:
                row_data += DICTIONARY[char.upper()][row] if char.isalpha() else DICTIONARY[char][row]
            row_data.append(0)  # Space between letters/numbers
        row_data += [0, 0, 0, 0, 0]  # Add extra space at the end for smooth scrolling
        text_grid.append(row_data)
    return text_grid

def generate_temperature_grid(temperature):
    """Generates a grid for the temperature including the degree symbol."""
    temp_str = str(temperature)
    temperature_grid = []
    for row in range(5):
        row_data = []
        for i, digit in enumerate(temp_str):
            row_data += DICTIONARY[digit][row]
            if i < len(temp_str) - 1:
                row_data.append(0)  # Space between digits
        row_data += DICTIONARY["DEGREE"][row]  # Add the degree symbol from DICTIONARY
        temperature_grid.append(row_data)
    return temperature_grid

def combine_grids(forecast_grid, temperature_grid, private_ip_grid, public_ip_grid):
    """Combines the forecast, temperature, private IP, and public IP grids into a full grid for display."""
    full_grid = [[0] * WIDTH for _ in range(HEIGHT)]

    # Display forecast at the top
    for row in range(5):
        visible_part = forecast_grid[row][:WIDTH]
        full_grid[row][:WIDTH] = visible_part

    # Display temperature below forecast
    for row in range(5):
        full_grid[6 + row][:WIDTH] = temperature_grid[row][:WIDTH]

    # Display private IP below temperature
    for row in range(5):
        full_grid[17 + row][:WIDTH] = private_ip_grid[row][:WIDTH]

    # Display public IP below private IP
    for row in range(5):
        full_grid[29 + row][:WIDTH] = public_ip_grid[row][:WIDTH]

    return full_grid
