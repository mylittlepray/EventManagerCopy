# venues/admin.py
from django.contrib import admin
from weather.models import WeatherSnapshot

@admin.register(WeatherSnapshot)
class WeatherSnapshotAdmin(admin.ModelAdmin):
    list_display = ('venue', 'created_at', 'temperature_celsius', 'weather_summary')
    
    list_filter = ('created_at', 'venue')
    
    list_display_links = ('venue', 'created_at')

    def weather_summary(self, obj):
        return f"T: {obj.temperature_celsius}°C, H: {obj.humidity_percent}%, W: {obj.wind_speed_ms}m/s"
    weather_summary.short_description = "Сводка"

    def has_add_permission(self, request):
        """Запрещаем создавать погоду вручную. Это делает Celery/API."""
        return False

    def has_change_permission(self, request, obj=None):
        """Запрещаем редактировать погоду. Это архивный слепок."""
        return False

    def has_delete_permission(self, request, obj=None):
        return True
