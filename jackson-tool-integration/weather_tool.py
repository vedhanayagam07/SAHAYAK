"""
Weather tool for SAHAYAK.
Fetches current weather from OpenWeatherMap API and determines if outdoor conditions
are suitable for a student study break.
"""

import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def get_weather(location: str) -> Dict[str, Any]:
    """
    Fetches the current weather for a given location using OpenWeatherMap API.

    Args:
        location: City name (e.g. "Bangalore", "London")

    Returns:
        Dict containing temperature, condition, outdoor break recommendation, and raw details.
    """
    if not location or not location.strip():
        return {
            "status": "error",
            "error": "Location cannot be empty.",
            "good_for_outdoor_break": "no"
        }

    clean_location = location.strip()
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key or api_key.strip() == "" or api_key == "YOUR_OPENWEATHER_API_KEY":
        return {
            "status": "error",
            "error": "OPENWEATHER_API_KEY is not configured or is a placeholder. Please set a valid OpenWeatherMap API key in .env.",
            "location": clean_location,
            "good_for_outdoor_break": "no"
        }

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": clean_location,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 404:
            return {
                "status": "error",
                "error": f"Location '{clean_location}' was not found by OpenWeatherMap.",
                "good_for_outdoor_break": "no"
            }
        elif response.status_code == 401:
            return {
                "status": "error",
                "error": "Invalid OpenWeatherMap API key. Check OPENWEATHER_API_KEY in .env.",
                "good_for_outdoor_break": "no"
            }
        
        response.raise_for_status()
        data = response.json()

        city_name = data.get("name", clean_location)
        country = data.get("sys", {}).get("country", "")
        temp = data.get("main", {}).get("temp")
        feels_like = data.get("main", {}).get("feels_like")
        humidity = data.get("main", {}).get("humidity")
        
        weather_list = data.get("weather", [])
        condition = weather_list[0].get("main", "Unknown") if weather_list else "Unknown"
        description = weather_list[0].get("description", "").capitalize() if weather_list else ""

        # Outdoor study break evaluation
        # Ideal range: 17°C <= temp <= 30°C and no rain/storm/extreme weather
        adverse_conditions = {"Rain", "Thunderstorm", "Snow", "Drizzle", "Tornado", "Squall", "Ash", "Sand"}
        
        is_adverse = condition in adverse_conditions
        is_temp_comfortable = (temp is not None and 17.0 <= temp <= 30.0)

        if is_adverse:
            good_for_break = "no"
            reason = f"Inclement weather ({description.lower()}). Better to stay indoors."
        elif temp is not None and temp < 17.0:
            good_for_break = "no"
            reason = f"Chilly ({temp:.1f}°C). If stepping out, bundle up warmly."
        elif temp is not None and temp > 30.0:
            good_for_break = "no"
            reason = f"Hot ({temp:.1f}°C). Stay hydrated and prefer indoor shaded areas."
        else:
            good_for_break = "yes"
            reason = f"Comfortable ({temp:.1f}°C, {description.lower()}). Great for fresh air!"

        return {
            "status": "success",
            "location": f"{city_name}, {country}" if country else city_name,
            "temperature_celsius": round(temp, 1) if temp is not None else None,
            "feels_like_celsius": round(feels_like, 1) if feels_like is not None else None,
            "humidity_percent": humidity,
            "condition": condition,
            "description": description,
            "good_for_outdoor_break": good_for_break,
            "outdoor_break_reason": reason
        }

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "Request timed out while contacting OpenWeatherMap.",
            "good_for_outdoor_break": "no"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"Failed to connect to weather service: {str(e)}",
            "good_for_outdoor_break": "no"
        }


if __name__ == "__main__":
    import sys
    test_loc = sys.argv[1] if len(sys.argv) > 1 else "Bangalore"
    print(f"Testing get_weather('{test_loc}')...")
    res = get_weather(test_loc)
    print(json.dumps(res, indent=2))
