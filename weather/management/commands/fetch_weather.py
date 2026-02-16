# weather/management/commands/fetch_weather.py
from django.core.management.base import BaseCommand
from venues.models import Venue
from weather.models import WeatherSnapshot
from weather.services import fetch_weather_for_venue

class Command(BaseCommand):
    help = "Fetch weather for all venues and create WeatherSnapshot"

    def handle(self, *args, **options):
        venues = Venue.objects.all()
        for venue in venues:
            self.stdout.write(f"Fetching weather for {venue.name}...")
            weather_data = fetch_weather_for_venue(venue)
            if weather_data:
                WeatherSnapshot.objects.create(venue=venue, **weather_data)
                self.stdout.write(self.style.SUCCESS(f"✓ Saved weather for {venue.name}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ Failed for {venue.name}"))
