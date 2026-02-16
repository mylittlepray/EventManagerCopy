# events/serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import Event, EventImage
from venues.serializers import VenueSerializer
from weather.serializers import WeatherSnapshotSerializer

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ["id", "image", "created_at"]


class EventListSerializer(serializers.ModelSerializer):
    venue = VenueSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title", 
            "description", 
            "publish_at", 
            "start_at", 
            "end_at", 
            "venue", 
            "rating", 
            "preview_image"
        ]

class EventDetailSerializer(serializers.ModelSerializer):
    venue = VenueSerializer(read_only=True)
    # weather = WeatherSnapshotSerializer(read_only=True)
    # images = EventImageSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title", 
            "description", 
            "publish_at", 
            "start_at", 
            "end_at", 
            "venue", 
            "rating", 
            "preview_image",
            "status",
            "author",
            # "weather",
            # "images",
        ]

    def to_representation(self, instance):
        """
        Динамическое скрытие полей для обычных пользователей.
        Если юзер НЕ суперюзер, убираем системные поля, но оставляем weather/images.
        """
        rep = super().to_representation(instance)
        request = self.context.get('request')

        # Если пользователь НЕ суперюзер (или аноним)
        if not request or not request.user.is_superuser:
            if 'status' in rep: rep.pop('status')
            if 'author' in rep: rep.pop('author')
            
        return rep

class EventWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ["author", "weather", "preview_image", "rating"] 
        
    def validate(self, data):
        start = data.get('start_at')
        end = data.get('end_at')
        if start and end and end <= start:
            raise serializers.ValidationError({"end_at": "Дата окончания должна быть позже начала."})
        return data

class EventImagesUploadSerializer(serializers.Serializer):
    images = serializers.ImageField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        files = request.FILES.getlist("images")
        if not files:
            raise serializers.ValidationError(
                {"images": "Upload at least one file using form-data key 'images'."}
            )
        attrs["images"] = files
        return attrs

class EventImagesResponseSerializer(serializers.Serializer):
    preview_image_url = serializers.SerializerMethodField()
    images = EventImageSerializer(many=True)

    @extend_schema_field(str)
    def get_preview_image_url(self, obj):
        request = self.context.get("request")
        event = obj["event"]
        if not event.preview_image:
            return None
        url = event.preview_image.url
        return request.build_absolute_uri(url) if request else url
    
class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()