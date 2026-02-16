# tests/test_celery_tasks.py
import pytest
from django.core import mail
from events.models import EventStatus, EmailNotificationConfig
from events.tasks import publish_scheduled_events_task
from django.utils import timezone
from datetime import timedelta
from django.test import override_settings

from weather.tasks import update_weather_snapshots
from weather.models import WeatherSnapshot

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_publish_chain_weather_and_email(event_factory, mocker):
    """
    Проверяет при наступлении даты publish_at: Планировщик -> Публикация -> Сигнал -> Погода + Email
    """
    mock_weather = mocker.patch('weather.tasks.get_forecast_for_time')
    mock_weather.return_value = {
        "temperature_celsius": 15.0,
        "humidity_percent": 60,
        "pressure_mmhg": 750,
        "wind_speed_ms": 3.0,
        "wind_direction": 90
    }

    EmailNotificationConfig.objects.create(
        subject_template="Ура! {title}",
        recipients_list="[email protected]",
        send_to_all_users=False
    )
    
    past = timezone.now() - timedelta(minutes=10)
    event = event_factory(status=EventStatus.SCHEDULED, publish_at=past)
    
    mail.outbox = []
    publish_scheduled_events_task()
    
    event.refresh_from_db()
    
    assert event.status == EventStatus.PUBLISHED
    
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["[email protected]"]
    
    mock_weather.assert_called_once()
    
    assert event.weather is not None
    assert event.weather.temperature_celsius == 15.0

@pytest.mark.django_db
def test_update_weather_snapshots_periodic(venue_factory, mocker):
    """
    Проверяет периодическую задачу сбора погоды для площадок.
    """
    v1 = venue_factory(name="Park Gorky")
    v2 = venue_factory(name="VDNH")
    
    mock_fetch = mocker.patch('weather.tasks.fetch_weather_for_venue')
    
    mock_fetch.side_effect = [
        { # Для v1
            "temperature_celsius": 20.0,
            "humidity_percent": 40,
            "pressure_mmhg": 760,
            "wind_speed_ms": 2.0,
            "wind_direction": 180
        },
        { # Для v2
            "temperature_celsius": 22.0,
            "humidity_percent": 45,
            "pressure_mmhg": 755,
            "wind_speed_ms": 3.0,
            "wind_direction": 200
        }
    ]
    
    results = update_weather_snapshots()
    
    assert mock_fetch.call_count == 2
    
    assert WeatherSnapshot.objects.count() == 2
    
    s1 = WeatherSnapshot.objects.get(venue=v1)
    assert s1.temperature_celsius == 20.0
    
    s2 = WeatherSnapshot.objects.get(venue=v2)
    assert s2.temperature_celsius == 22.0
    
    assert "Updated Park Gorky" in results
    assert "Updated VDNH" in results