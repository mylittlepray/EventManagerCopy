# events/models.py
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, F

from venues.models import Venue
from weather.models import WeatherSnapshot

class EventStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SCHEDULED = "SCHEDULED", "Scheduled"
    PUBLISHED = "PUBLISHED", "Published"
    ENDED = "ENDED", "Ended"
    DELETED = "DELETED", "Deleted"


class Event(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    start_at = models.DateTimeField(verbose_name="Начало")
    end_at = models.DateTimeField(verbose_name="Окончание")
    publish_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата публикации")

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="Автор",
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="Место проведения",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(25)],
        default=0,
        verbose_name="Рейтинг",
    )

    status = models.CharField(
        max_length=16,
        choices=EventStatus.choices,
        default=EventStatus.DRAFT,
        db_index=True,
        verbose_name="Статус",
    )

    # Превью-изображение (позже сделаем автогенерацию 200px)
    preview_image = models.ImageField(
        upload_to="events/previews/",
        null=True,
        blank=True,
        editable=False,
        verbose_name="Обложка",
    )

    weather = models.OneToOneField(
        WeatherSnapshot, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='event',
        verbose_name="Погода",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=0) & Q(rating__lte=25),
                name="event_rating_0_25",
            ),
            models.CheckConstraint(
                condition=Q(end_at__gt=F("start_at")),
                name="event_end_after_start",
            ),
        ]

    def __str__(self):
        return self.title


class EventImage(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to='events/images/', verbose_name="Файл")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Галерея"

    def __str__(self):
        return f"Image for event_id={self.event_id}"

class EmailNotificationConfig(models.Model):
    """
    Настройки для автоматической рассылки при публикации мероприятия.
    Предполагается, что существует только одна запись (Singleton).
    """
    subject_template = models.CharField(
        max_length=255, 
        default="Новое мероприятие: {title}",
        verbose_name="Шаблон темы письма",
        help_text="Используйте {title}, {date}, {venue} для подстановки значений."
    )
    message_template = models.TextField(
        default="Приглашаем вас на {title}!\nМесто: {venue}\nДата: {date}\nОписание: {description}",
        verbose_name="Шаблон текста письма",
        help_text="Используйте {title}, {date}, {venue}, {description} для подстановки."
    )

    recipients_list = models.TextField(
        blank=True, 
        default="",
        verbose_name="Список адресатов (вручную)",
        help_text="Введите email адреса через запятую."
    )
    send_to_all_users = models.BooleanField(
        default=True,
        verbose_name="Отправлять всем зарегистрированным пользователям"
    )

    def save(self, *args, **kwargs):
        if not self.pk and EmailNotificationConfig.objects.exists():
            pass 
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Настройки Email уведомлений"

    class Meta:
        verbose_name = "Настройки рассылки"
        verbose_name_plural = "Настройки рассылки"