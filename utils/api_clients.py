import requests
import json
from config import settings

def get_live_weather_data(city_name):
    if not settings.OPENWEATHERMAP_API_KEY or settings.OPENWEATHERMAP_API_KEY == "YOUR_ACTUAL_OPENWEATHERMAP_API_KEY_HERE":
        if settings.DEBUG_MODE:
            print("API Client Error: OpenWeatherMap API key not configured or is placeholder.")
        return None
    if not city_name:
        if settings.DEBUG_MODE:
            print("API Client Error: City name not provided for weather data.")
        return None

    params = {
        'q': city_name + ",IN",
        'appid': settings.OPENWEATHERMAP_API_KEY,
        'units': 'metric',
        'lang': 'hi'
    }
    headers = { # Added a common User-Agent
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(settings.OPENWEATHERMAP_BASE_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        
        if weather_data.get("cod") != 200: # Check API specific status code
             if settings.DEBUG_MODE:
                 print(f"API Client Warning: Weather API returned status {weather_data.get('cod')} for {city_name}. Message: {weather_data.get('message')}")
             return None
        return weather_data
    except requests.exceptions.HTTPError as http_err:
        if settings.DEBUG_MODE: print(f"API Client HTTP error for {city_name}: {http_err} - Response: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        if settings.DEBUG_MODE: print(f"API Client Network error for {city_name}: {req_err}")
        return None
    except json.JSONDecodeError as json_err:
        if settings.DEBUG_MODE: print(f"API Client JSON decode error for {city_name}: {json_err}")
        return None

if __name__ == '__main__':
    print("Testing API Clients...")
    if not settings.OPENWEATHERMAP_API_KEY or settings.OPENWEATHERMAP_API_KEY == "YOUR_ACTUAL_OPENWEATHERMAP_API_KEY_HERE":
        print("WARNING: OpenWeatherMap API key is not set in .env or is still the placeholder.")
        print("Skipping live API test.")
    else:
        print("\n--- Testing Weather API Client ---")
        test_city = "Delhi" # A city from your KNOWN_LOCATIONS_FOR_WEATHER
        data = get_live_weather_data(test_city)
        if data:
            print(f"Successfully fetched weather data for {test_city}:")
            temp = data.get('main', {}).get('temp')
            description = data.get('weather', [{}])[0].get('description')
            humidity = data.get('main', {}).get('humidity')
            print(f"  Temperature: {temp}°C")
            print(f"  Condition: {description}")
            print(f"  Humidity: {humidity}%")
        else:
            print(f"Failed to fetch weather data for {test_city}.")