from rest_framework import serializers
from .models import WeatherSnapshot

class WeatherSnapshotSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source="venue.name", read_only=True)

    class Meta:
        model = WeatherSnapshot
        fields = [
            "id",
            "venue",
            "venue_name",
            "temperature_celsius",
            "humidity_percent",
            "pressure_mmhg",
            "wind_direction",
            "wind_speed_ms",
            "created_at",
        ]
        read_only_fields = ["created_at"]
