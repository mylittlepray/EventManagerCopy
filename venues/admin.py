# venues/admin.py
from django.contrib import admin
from venues.models import Venue

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_coords', 'id')
    search_fields = ('name',)

    def location_coords(self, obj):
        if obj.location:
            return f"{obj.location.y}, {obj.location.x}"
        return "-"
    location_coords.short_description = "Координаты (Lat, Lon)"