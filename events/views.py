# events/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from core.permissions import IsSuperUserOrReadOnly
from .models import Event, EventImage, EventStatus
from .serializers import EventImageSerializer, EventImagesUploadSerializer, EventImagesResponseSerializer, FileUploadSerializer, EventListSerializer, EventDetailSerializer, EventWriteSerializer
from .services import make_preview
from .xlsx_services import export_events_to_xlsx, import_events_from_xlsx
from .filters import EventFilter

from venues.services import get_venue_coordinates

from weather.serializers import WeatherSnapshotSerializer
from weather.models import WeatherSnapshot
from weather.services import get_forecast_for_time

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        tags=["Мероприятия"],
        summary="Список мероприятий",
        description=(
            "Обычный пользователь видит только мероприятия со статусом PUBLISHED. "
            "Суперпользователь видит все статусы.\n\n"
            "Поддерживаются пагинация, поиск, сортировка и фильтрация."
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
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Поиск по названию мероприятия (title) и названию места (venue__name).",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Сортировка: title, start_at, end_at. Пример: ordering=-start_at",
            ),
            OpenApiParameter(
                name="rating_min",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Минимальный рейтинг (0..25).",
            ),
            OpenApiParameter(
                name="rating_max",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Максимальный рейтинг (0..25).",
            ),
            OpenApiParameter(
                name="start_at_after",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Начало мероприятия от (>=). Пример: 2026-01-01T00:00:00Z",
            ),
            OpenApiParameter(
                name="start_at_before",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Начало мероприятия до (<=).",
            ),
            OpenApiParameter(
                name="end_at_after",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Окончание мероприятия от (>=).",
            ),
            OpenApiParameter(
                name="end_at_before",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Окончание мероприятия до (<=).",
            ),
            OpenApiParameter(
                name="venue",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                many=True,
                description="Фильтр по месту проведения (можно несколько): ?venue=1&venue=2",
            ),
        ],
        responses={
            200: OpenApiResponse(response=EventListSerializer(many=True), description="Список мероприятий."),
            403: OpenApiResponse(description="Недостаточно прав (например, попытка создать/изменить без superuser)."),
        },
    ),
    retrieve=extend_schema(
        tags=["Мероприятия"],
        summary="Детали мероприятия",
        description="Обычный пользователь может получить только PUBLISHED. Суперпользователь — любые статусы.",
        responses={
            200: OpenApiResponse(response=EventDetailSerializer, description="Детали мероприятия."),
            404: OpenApiResponse(description="Мероприятие не найдено или скрыто (не PUBLISHED для обычного пользователя)."),
        },
    ),
    create=extend_schema(
        tags=["Мероприятия"],
        summary="Создать мероприятие",
        description="Доступно только суперпользователю. Автор проставляется автоматически.",
        responses={
            201: OpenApiResponse(response=EventDetailSerializer, description="Мероприятие создано."),
            403: OpenApiResponse(description="Только для superuser."),
        },
    ),
    update=extend_schema(
        tags=["Мероприятия"],
        summary="Обновить мероприятие",
        description="Доступно только суперпользователю.",
        responses={200: OpenApiResponse(response=EventDetailSerializer), 403: OpenApiResponse(description="Только для superuser.")},
    ),
    partial_update=extend_schema(
        tags=["Мероприятия"],
        summary="Частично обновить мероприятие",
        description="Доступно только суперпользователю.",
        responses={200: OpenApiResponse(response=EventDetailSerializer), 403: OpenApiResponse(description="Только для superuser.")},
    ),
    destroy=extend_schema(
        tags=["Мероприятия"],
        summary="Удалить мероприятие (soft delete)",
        description="Доступно только суперпользователю. Физически запись не удаляется, статус становится DELETED.",
        responses={204: OpenApiResponse(description="Помечено как DELETED."), 403: OpenApiResponse(description="Только для superuser.")},
    ),
    export_xlsx=extend_schema(
        tags=["Мероприятия / XLSX"],
        summary="Экспорт мероприятий в XLSX",
        description="Экспортирует текущий отфильтрованный список мероприятий в Excel. Фильтры и поиск такие же, как в списке.",
        responses={
            200: OpenApiResponse(
                description="XLSX файл (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)."
            )
        },
    ),
    import_xlsx=extend_schema(
        tags=["Мероприятия / XLSX"],
        summary="Импорт мероприятий из XLSX",
        description=(
            "Доступно только суперпользователю. "
            "Принимает multipart/form-data с файлом в поле file. "
            "Если в файле есть некорректные строки, они вернутся в errors."
        ),
        request=FileUploadSerializer,
        responses={
            201: OpenApiResponse(description="Импорт завершён успешно."),
            400: OpenApiResponse(description="Ошибки импорта (невалидные строки или файл не передан)."),
            403: OpenApiResponse(description="Только для superuser."),
        },
        examples=[
            OpenApiExample(
                name="Пример частичного импорта с ошибками",
                value={
                    "message": "Created 1 events.",
                    "errors": ["Row 2: End time must be after start time"],
                },
                response_only=True,
                status_codes=["400"],
            )
        ],
    ),
)
class EventViewSet(ModelViewSet):
    permission_classes = [IsSuperUserOrReadOnly]
    filterset_class = EventFilter

    search_fields = [
        "title",
        "venue__name",
    ]

    ordering_fields = [
        "title",
        "start_at",
        "end_at",
    ]
    ordering = ["start_at"] 

    def get_queryset(self):
        qs = Event.objects.select_related("venue", "author")
        
        # if self.action == 'retrieve':
        #    qs = qs.prefetch_related("images", "weather")

        user = self.request.user
        if user.is_authenticated and user.is_superuser:
            return qs
        return qs.filter(status=EventStatus.PUBLISHED)

    def get_serializer_class(self):
        """
        Выбор сериализатора в зависимости от действия.
        """
        if self.action == 'list':
            return EventListSerializer
        
        if self.action == 'retrieve':
            return EventDetailSerializer
            
        if self.action in ['create', 'update', 'partial_update']:
            return EventWriteSerializer
            
        if self.action == "images_upload":
            return EventImagesUploadSerializer
            
        return EventDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        instance.status = EventStatus.DELETED
        instance.save(update_fields=["status"])

    @action(detail=True, methods=[], url_path="images", parser_classes=[MultiPartParser, FormParser])
    def images(self, request, pk=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @images.mapping.get
    @extend_schema(
        tags=["Мероприятия / Изображения"],
        summary="Список изображений мероприятия",
        description="Возвращает preview_image_url и список загруженных изображений мероприятия.",
        responses={200: EventImagesResponseSerializer, 404: OpenApiResponse(description="Не найдено.")},
    )
    def images_list(self, request, pk=None):
        event = self.get_object()
        qs = event.images.all().order_by("-created_at")

        payload = {"event": event, "images": qs}
        data = EventImagesResponseSerializer(payload, context={"request": request}).data
        return Response(data)

    @images.mapping.post
    @extend_schema(
        tags=["Мероприятия / Изображения"],
        summary="Загрузка изображений мероприятия",
        description=(
            "Доступно только суперпользователю. "
            "Принимает multipart/form-data с ключом images (можно несколько файлов). "
            "Превью генерируется один раз при первой загрузке и далее не перезаписывается."
        ),
        request=EventImagesUploadSerializer,
        responses={
            201: OpenApiResponse(response=EventImageSerializer(many=True), description="Изображения загружены."),
            400: OpenApiResponse(description="Файлы не переданы или неверный формат."),
            403: OpenApiResponse(description="Только для superuser."),
        },
        examples=[
            OpenApiExample(
                name="Пример ошибки (нет файлов)",
                value={"images": ["Upload at least one file using form-data key 'images'."]},
                response_only=True,
                status_codes=["400"],
            )
        ],
    )
    def images_upload(self, request, pk=None):
        event = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        files = serializer.validated_data["images"]

        created = []
        for f in files:
            created.append(EventImage.objects.create(event=event, image=f))

        if not event.preview_image and created:
            first = created[0]
            first.image.open("rb")
            preview_content = make_preview(first.image.file, min_side=200)
            event.preview_image.save(
                f"event_{event.id}_preview.jpg",
                preview_content,
                save=True,
            )

        return Response(
            EventImageSerializer(created, many=True, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    
    @action(detail=False, methods=["get"], url_path="export-xlsx")
    def export_xlsx(self, request):
        """
        Экспорт отфильтрованных событий в XLSX.
        """
        # Используем filter_queryset, чтобы применились те же фильтры, что и в списке
        queryset = self.filter_queryset(self.get_queryset())
        return export_events_to_xlsx(queryset)

    @action(detail=False, methods=["post"], url_path="import-xlsx", parser_classes=[MultiPartParser, FormParser], serializer_class=FileUploadSerializer)
    def import_xlsx(self, request):
        """
        Импорт событий из XLSX.
        """
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # Вызываем сервис импорта
        result = import_events_from_xlsx(file_obj, request.user)
        
        if result["errors"]:
            return Response({
                "message": f"Created {result['created']} events.",
                "errors": result["errors"]
            }, status=status.HTTP_400_BAD_REQUEST) # Или 200, если частичный успех ок
            
        return Response({"message": f"Successfully imported {result['created']} events."}, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        tags=["Мероприятия / Погода"],
        summary="Получить погоду для события",
        description="Возвращает сохраненный прогноз погоды. Если прогноза нет в БД, пытается получить его онлайн и сохранить.",
        responses={200: WeatherSnapshotSerializer, 404: OpenApiResponse(description="Прогноз недоступен")}
    )
    @action(detail=True, methods=['get'], url_path='weather')
    def get_weather(self, request, pk=None):
        event = self.get_object()

        if event.weather:
            serializer = WeatherSnapshotSerializer(event.weather)
            return Response(serializer.data)

        if not event.venue or not event.venue.location:
            return Response(
                {"detail": "У события не указана площадка или координаты."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lat, lon = get_venue_coordinates(event.venue)

        weather_data = get_forecast_for_time(
            float(lat), 
            float(lon), 
            event.start_at
        )

        if not weather_data:
            return Response(
                {"detail": "Прогноз погоды на эту дату пока недоступен (или дата слишком далеко)."},
                status=status.HTTP_404_NOT_FOUND
            )

        snapshot = WeatherSnapshot.objects.create(
            venue=event.venue,
            **weather_data
        )
        
        event.weather = snapshot
        event.save(update_fields=['weather'])

        serializer = WeatherSnapshotSerializer(snapshot)
        return Response(serializer.data)