# events/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from .models import Event, EventStatus

@shared_task
def send_event_notification_task(event_id, subject, message, recipient_list):
    """
    Асинхронная отправка email.
    """
    try:
        event = Event.objects.get(id=event_id)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return f"Email sent for event {event.title}"
    except Event.DoesNotExist:
        return "Event not found"
    except Exception as e:
        return f"Error sending email: {e}"

@shared_task
def publish_scheduled_events_task():
    """
    Периодическая задача: ищет черновики, у которых наступило время публикации.
    """
    now = timezone.now()
    # Ищем события: статус SCHEDULED и publish_at <= сейчас
    events_to_publish = Event.objects.filter(
        status=EventStatus.SCHEDULED,
        publish_at__lte=now
    )
    
    count = events_to_publish.count()
    if count > 0:
        for event in events_to_publish:
            event.status = EventStatus.PUBLISHED
            event.save(update_fields=['status']) # Это вызовет сигнал post_save
            
        return f"Published {count} events."
    return "No events to publish."
