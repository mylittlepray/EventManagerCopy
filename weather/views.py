# weather.views.py
from rest_framework.viewsets import ReadOnlyModelViewSet

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from .models import WeatherSnapshot
from .serializers import WeatherSnapshotSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Погода"],
        summary="Список снимков погоды",
        description=(
            "Возвращает снимки погоды по площадкам (Venue). "
            "Обычно используется, чтобы получить текущую/последнюю сохранённую погоду для площадок."
        ),
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Номер страницы пагинации.",
            ),
            OpenApiParameter(
                name="venue",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Фильтр по площадке (Venue id), если реализован на роутере/фильтрах.",
            ),
        ],
        responses={
            200: OpenApiResponse(response=WeatherSnapshotSerializer(many=True), description="Список снимков погоды."),
        },
    ),
    retrieve=extend_schema(
        tags=["Погода"],
        summary="Детали снимка погоды",
        description="Возвращает один снимок погоды по его id.",
        responses={
            200: OpenApiResponse(response=WeatherSnapshotSerializer, description="Снимок погоды."),
            404: OpenApiResponse(description="Снимок погоды не найден."),
        },
    ),
)
class WeatherSnapshotViewSet(ReadOnlyModelViewSet):
    queryset = WeatherSnapshot.objects.select_related("venue")
    serializer_class = WeatherSnapshotSerializer