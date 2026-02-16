# weather/models.py
from django.db import models
from venues.models import Venue

class WeatherSnapshot(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="weather_snapshots", verbose_name="Площадка")
    temperature_celsius = models.FloatField(verbose_name="Температура (°C)")
    humidity_percent = models.IntegerField(verbose_name="Влажность (%)")
    pressure_mmhg = models.IntegerField(verbose_name="Давление (мм рт.ст.)")
    wind_direction = models.CharField(max_length=10, verbose_name="Направление ветра", help_text="Направление ветра (N/NE/E/SE/S/SW/W/NW)")
    wind_speed_ms = models.FloatField(verbose_name="Скорость ветра (м/с)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    class Meta:
        verbose_name = "Снимок погоды"
        verbose_name_plural = "Архив погоды"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Weather at {self.venue.name} on {self.created_at}"
