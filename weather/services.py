# weather/services.py
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from venues.services import get_venue_coordinates

def degrees_to_direction(degrees):
    """Преобразует градусы направления ветра в текстовые обозначения."""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]

def hpa_to_mmhg(hpa):
    """Преобразует давление из гПа (гектопаскалей) в мм рт.ст."""
    return hpa * 0.75006

def fetch_weather_for_venue(venue):
    """
    Получает текущую погоду для venue через Open-Meteo API.
    Возвращает словарь с данными погоды или None при ошибке.
    """
    lat, lon = get_venue_coordinates(venue)

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m"
        f"&timezone=auto"
    )

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})

        return {
            "temperature_celsius": current.get("temperature_2m", 0.0),
            "humidity_percent": current.get("relative_humidity_2m", 0.0),
            "pressure_mmhg": hpa_to_mmhg(current.get("surface_pressure", 1013.0)),
            "wind_speed_ms": current.get("wind_speed_10m", 0.0),
            "wind_direction": degrees_to_direction(current.get("wind_direction_10m", 0.0)),
        }
    except Exception as e:
        print(f"Error fetching weather for {venue.name}: {e}")
        return None

def get_forecast_for_time(lat, lon, target_datetime):
    """
    Получает прогноз погоды на конкретный час.
    target_datetime: datetime объект (start_at события)
    """

    date_str = target_datetime.strftime('%Y-%m-%d')
    hour_str = target_datetime.strftime('%Y-%m-%dT%H:00')

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m",
        "start_date": date_str,
        "end_date": date_str,
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        hourly_data = data.get("hourly", {})
        times = hourly_data.get("time", [])
        
        try:
            index = -1
            for i, t in enumerate(times):
                if t.startswith(hour_str):
                    index = i
                    break
            
            if index == -1:
                return None

            return {
                "temperature_celsius": hourly_data["temperature_2m"][index],
                "humidity_percent": hourly_data["relative_humidity_2m"][index],
                "pressure_mmhg": int(hourly_data["pressure_msl"][index] * 0.75006),
                "wind_speed_ms": hourly_data["wind_speed_10m"][index],
                "wind_direction": hourly_data["wind_direction_10m"][index],
            }

        except (ValueError, IndexError):
            return None

    except Exception as e:
        print(f"Weather API Error: {e}")
        return None
