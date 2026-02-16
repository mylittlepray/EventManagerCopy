# venues/serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Venue

@extend_schema_serializer(
    examples=[
         OpenApiExample(
            'Пример ответа',
            value={
                'id': 1,
                'name': 'Arena',
                'location': {'latitude': 55.0, 'longitude': 92.0}
            },
            response_only=True,
        )
    ]
)
class VenueSerializer(serializers.ModelSerializer):
    location = serializers.CharField(write_only=True)

    class Meta:
        model = Venue
        fields = ['id', 'name', 'location']
        extra_kwargs = {'location': {'required': True}}

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.location:
            ret['location'] = {
                "latitude": instance.location.y,
                "longitude": instance.location.x
            }
        return ret