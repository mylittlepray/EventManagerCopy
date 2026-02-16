# events/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import EventImage, Event, EventStatus, EmailNotificationConfig
from django.contrib.auth.models import User

from events.services import make_preview 

from events.tasks import send_event_notification_task
from weather.tasks import set_event_weather_forecast_task

@receiver(post_save, sender=EventImage)
def generate_preview_on_save(sender, instance, created, **kwargs):
    """
    Автоматически создаёт превью для события, если его нет,
    при добавлении новой картинки.
    """
    if created:
        event = instance.event
        if not event.preview_image and instance.image:
            instance.image.open()
            preview_content = make_preview(instance.image.file)
            
            event.preview_image.save(
                f'preview_{event.id}.jpg',
                preview_content,
                save=True
            )

@receiver(post_delete, sender=EventImage)
def update_preview_on_delete(sender, instance, **kwargs):
    """
    Если удалили картинку, которая была превью, можно попробовать 
    поставить другую (опционально).
    """
    pass 

@receiver(pre_save, sender=Event)
def reset_weather_on_change(sender, instance, **kwargs):
    if instance.status != EventStatus.PUBLISHED:
        return 

    if not instance.pk:
        instance._need_weather_update = True
        return

    try:
        old_instance = Event.objects.get(pk=instance.pk)

        if old_instance.status != EventStatus.PUBLISHED and instance.status == EventStatus.PUBLISHED:
            instance._need_weather_update = True
            return

        if old_instance.start_at != instance.start_at or old_instance.venue != instance.venue:
            instance.weather = None 
            instance._need_weather_update = True
            
    except Event.DoesNotExist:
        instance._need_weather_update = True

@receiver(post_save, sender=Event)
def trigger_weather_update(sender, instance, created, **kwargs):
    """
    Запускает задачу обновления погоды, если был установлен флаг в pre_save.
    """
    if getattr(instance, '_need_weather_update', False):
        set_event_weather_forecast_task.delay(instance.id)

@receiver(post_save, sender=Event)
def event_published_notification(sender, instance, created, update_fields=None, **kwargs):
    # Если статус не PUBLISHED, нам тут делать нечего
    if instance.status != EventStatus.PUBLISHED:
        return
        
    # 2. ПРОВЕРКА НА ИЗМЕНЕНИЕ СТАТУСА (Anti-Spam защита)
    # Если это не создание объекта (created=False)
    # И при этом update_fields передан
    # И в update_fields НЕТ поля 'status'
    # ЗНАЧИТ: Мы обновляем что-то другое (погоду, картинку), но не статус.
    # Письмо слать НЕ НАДО.
    if not created and update_fields and 'status' not in update_fields:
        return

    config = EmailNotificationConfig.objects.first()
    if not config:
        return

    recipients = set()
        
    if config.recipients_list:
        emails = [e.strip() for e in config.recipients_list.split(",") if e.strip()]
        recipients.update(emails)
            
    if config.send_to_all_users:
        users_emails = User.objects.filter(email__isnull=False).exclude(email='').values_list('email', flat=True)
        recipients.update(users_emails)

    if not recipients:
        return

    context = {
        "title": instance.title,
        "venue": instance.venue.name if instance.venue else "Не указано",
        "date": str(instance.start_at),
        "description": instance.description or ""
    }

    try:
        subject = config.subject_template.format(**context)
        message = config.message_template.format(**context)
    except KeyError:
        subject = f"Новое мероприятие: {instance.title}"
        message = f"Приглашаем на {instance.title} ({instance.start_at})"

    send_event_notification_task.delay(
        event_id=instance.id,
        subject=subject,
        message=message,
        recipient_list=list(recipients)
    )