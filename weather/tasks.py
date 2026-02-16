from celery import shared_task
from events.models import Event
from venues.models import Venue
from weather.models import WeatherSnapshot
from weather.services import fetch_weather_for_venue, get_forecast_for_time

from venues.services import get_venue_coordinates

@shared_task
def update_weather_snapshots():
    """
    Периодическая задача: пробегается по всем Venues и сохраняет погоду.
    """
    venues = Venue.objects.all()
    results = []
    for venue in venues:
        weather_data = fetch_weather_for_venue(venue)
        if weather_data:
            WeatherSnapshot.objects.create(venue=venue, **weather_data)
            results.append(f"Updated {venue.name}")
        else:
            results.append(f"Failed {venue.name}")
    return results

@shared_task
def set_event_weather_forecast_task(event_id):
    try:
        event = Event.objects.get(id=event_id)
        
        if not event.venue or not event.venue.location:
             return "No venue or location"

        lat, lon = get_venue_coordinates(event.venue)

        weather_data = get_forecast_for_time(
            float(lat), 
            float(lon), 
            event.start_at
        )

        if not weather_data:
            return "Weather forecast not available (too far in future?)"

        snapshot = WeatherSnapshot.objects.create(
            venue=event.venue,
            **weather_data
        )

        event.weather = snapshot
        event.save(update_fields=['weather'])
        
        return f"Weather saved for event {event.title}"

    except Event.DoesNotExist:
        return "Event not found"