# venues/services.py
from django.contrib.gis.geos import Point

def get_venue_coordinates(venue):
    """
    Извлекает (lat, lon) из объекта Venue, обрабатывая разные форматы location.
    Возвращает кортеж (lat, lon) или (None, None).
    """
    if not venue or not venue.location:
        return None, None

    loc = venue.location
    lat, lon = None, None

    # 1. Если это уже объект GEOSGeometry/Point
    if hasattr(loc, 'x') and hasattr(loc, 'y'):
        lon = loc.x
        lat = loc.y

    # 2. Если это строка (WKT)
    elif isinstance(loc, str):
        try:
            p = Point.from_ewkt(loc)
            lon = p.x
            lat = p.y
        except Exception:
            pass
    
    # 3. Валидация диапазонов (защита от перепутанных Lat/Lon)
    if lat is not None and lon is not None:
        try:
            lat = float(lat)
            lon = float(lon)
            if abs(lat) > 90 and abs(lon) <= 90:
                lat, lon = lon, lat
        except ValueError:
            return None, None

    return lat, lon
