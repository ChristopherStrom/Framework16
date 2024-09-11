# weather.py
import requests
from settings import LATITUDE, LONGITUDE, DEBUG

LOCATION_API = f"http://ip-api.com/json/"

def get_nws_forecast_url():
    latitude = LATITUDE
    longitude = LONGITUDE
    try:
        #try and pull location data
        response = requests.get(LOCATION_API)
        data = response.json()
        latitude = data['lat']
        longitude = data['lon']
    except Exception as e:
        if DEBUG:
            print(f"Error fetching location URL: {e}")

    try:  
        NWS_POINTS_API = f"https://api.weather.gov/points/{latitude},{longitude}"
        response = requests.get(NWS_POINTS_API)
        data = response.json()
        forecast_url = data['properties']['forecastHourly']
        print(NWS_POINTS_API)
        return forecast_url
    except Exception as e:
        if DEBUG:
            print(f"Error fetching forecast URL: {e}")
            print(NWS_POINTS_API)
        return None

def get_current_temperature_and_icon_from_forecast(forecast_url):
    try:
        response = requests.get(forecast_url)
        forecast_data = response.json()
        current_period = forecast_data['properties']['periods'][0]
        current_temp = current_period['temperature']
        short_forecast = current_period['shortForecast']
        return current_temp, short_forecast
    except Exception as e:
        if DEBUG:
            print(f"Error getting forecast data: {e}")
        return None, None

def get_forecast_text(short_forecast):
    short_forecast = short_forecast.lower()
    if "cloud" in short_forecast:
        return 'Cloudy'
    elif "sun" in short_forecast or "clear" in short_forecast:
        return 'Sunny'
    elif "rain" in short_forecast or "showers" in short_forecast:
        return 'Rain'
    elif "snow" in short_forecast:
        return 'Snow'
    elif "thunderstorm" in short_forecast:
        return 'Storm'
    elif "wind" in short_forecast:
        return 'Windy'
    elif "fog" in short_forecast:
        return 'Fog'
    elif "haze" in short_forecast:
        return 'Hazy'
    else:
        return 'N/A'
