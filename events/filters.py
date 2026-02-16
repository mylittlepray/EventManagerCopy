# events/filters.py
import django_filters
from .models import Event

from venues.models import Venue

class EventFilter(django_filters.FilterSet):
    start_from = django_filters.IsoDateTimeFilter(field_name="start_at", lookup_expr="gte")
    start_to = django_filters.IsoDateTimeFilter(field_name="start_at", lookup_expr="lte")

    end_from = django_filters.IsoDateTimeFilter(field_name="end_at", lookup_expr="gte")
    end_to = django_filters.IsoDateTimeFilter(field_name="end_at", lookup_expr="lte")

    rating_min = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")
    rating_max = django_filters.NumberFilter(field_name="rating", lookup_expr="lte")

    venue = django_filters.ModelMultipleChoiceFilter(
        field_name="venue",
        to_field_name="id",
        queryset=Venue.objects.all(),
    )

    class Meta:
        model = Event
        fields = ['venue', 'status']
