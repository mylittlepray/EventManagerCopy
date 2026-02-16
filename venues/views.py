# venues/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiExample

from core.permissions import IsSuperUserOrPublicReadIfAllowed
from .models import Venue
from .serializers import VenueSerializer

from weather.serializers import WeatherSnapshotSerializer
from weather.models import WeatherSnapshot

@extend_schema_view(
    list=extend_schema(
        tags=["Площадки"],
        summary="Список площадок",
        description="Возвращает список площадок (мест проведения).",
        responses={
            200: OpenApiResponse(response=VenueSerializer(many=True), description="Список площадок."),
            403: OpenApiResponse(description="Только для superuser (если публичный доступ отключен)."),
        },
    ),
    retrieve=extend_schema(
        tags=["Площадки"],
        summary="Детали площадки",
        description="Возвращает одну площадку по её id.",
        responses={
            200: OpenApiResponse(response=VenueSerializer, description="Площадка."),
            403: OpenApiResponse(description="Только для superuser."),
            404: OpenApiResponse(description="Площадка не найдена."),
        },
    ),
    create=extend_schema(
        tags=["Площадки"],
        summary="Создать площадку",
        description="Создаёт площадку. Поле location принимает строку WKT 'POINT(lon lat)'.",
        examples=[
            OpenApiExample(
                "Пример создания",
                value={
                    "name": "Центральный стадион",
                    "location": "POINT(92.8526 56.0106)",
                },
                request_only=True
            )
        ],
        responses={
            201: OpenApiResponse(response=VenueSerializer, description="Площадка создана."),
            400: OpenApiResponse(description="Ошибка валидации."),
            403: OpenApiResponse(description="Только для superuser."),
        },
    ),
    update=extend_schema(
        tags=["Площадки"],
        summary="Обновить площадку",
        description="Полное обновление площадки (PUT).",
        examples=[
            OpenApiExample(
                "Пример обновления",
                value={
                    "name": "Новое название",
                    "location": "POINT(30.0 60.0)",
                },
                request_only=True
            )
        ],
        responses={
            200: OpenApiResponse(response=VenueSerializer, description="Площадка обновлена."),
            400: OpenApiResponse(description="Ошибка валидации."),
            403: OpenApiResponse(description="Только для superuser."),
            404: OpenApiResponse(description="Площадка не найдена."),
        },
    ),
    partial_update=extend_schema(
        tags=["Площадки"],
        summary="Частично обновить площадку",
        description="Частичное обновление площадки (PATCH).",
        examples=[
            OpenApiExample(
                "Пример частичного обновления",
                value={
                    "location": "POINT(93.0 56.5)"
                },
                request_only=True
            )
        ],
        responses={
            200: OpenApiResponse(response=VenueSerializer, description="Площадка обновлена."),
            400: OpenApiResponse(description="Ошибка валидации."),
            403: OpenApiResponse(description="Только для superuser."),
            404: OpenApiResponse(description="Площадка не найдена."),
        },
    ),
    destroy=extend_schema(
        tags=["Площадки"],
        summary="Удалить площадку",
        description="Удаляет площадку.",
        responses={
            204: OpenApiResponse(description="Площадка удалена."),
            403: OpenApiResponse(description="Только для superuser."),
            404: OpenApiResponse(description="Площадка не найдена."),
        },
    ),
)
class VenueViewSet(ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    permission_classes = [IsSuperUserOrPublicReadIfAllowed]

    @extend_schema(
        tags=["Площадки / Погода"],
        summary="История погоды на площадке",
        description="Возвращает список всех сохраненных снимков погоды для данной площадки.",
        responses={
            200: WeatherSnapshotSerializer(many=True),
            404: OpenApiResponse(description="Площадка не найдена"),
        }
    )
    @action(detail=True, methods=['get'])
    def weather(self, request, pk=None):
        """
        GET /api/venues/{id}/weather/
        Возвращает список снимков погоды для конкретной площадки.
        """
        venue = self.get_object()
        
        snapshots = WeatherSnapshot.objects.filter(venue=venue).order_by('-created_at')
        
        page = self.paginate_queryset(snapshots)
        if page is not None:
            serializer = WeatherSnapshotSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = WeatherSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)