# ipaddresses.py
import socket
import requests
from settings import DEBUG

def get_private_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        if DEBUG:
            print(f"Error fetching private IP: {e}")
        return " "

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org', params={'format': 'text'})
        return response.text
    except Exception as e:
        if DEBUG:
            print(f"Error fetching public IP: {e}")
        return " "
