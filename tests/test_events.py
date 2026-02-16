# tests/test_events.py
import pytest
from django.urls import reverse
from events.models import EventStatus

@pytest.mark.django_db
def test_create_event_invalid_dates(api_client, user_factory, venue_factory):
    """Проверка валидации дат"""
    admin = user_factory(is_superuser=True)
    venue = venue_factory()
    api_client.force_authenticate(user=admin)
    
    data = {
        "title": "Bad Date Event",
        "start_at": "2026-05-01T20:00:00Z",
        "end_at": "2026-05-01T19:00:00Z", # <-- Ошибка
        "venue": venue.id,
    }
    
    url = reverse('events-list')
    response = api_client.post(url, data)
    
    assert response.status_code == 400
    assert 'end_at' in str(response.data) or 'non_field_errors' in str(response.data)

@pytest.mark.django_db
def test_event_list_permissions(api_client, event_factory, user_factory):
    """Проверка видимости: юзер - только PUBLISHED, админ - ВСЕ"""
    pub_event = event_factory(status=EventStatus.PUBLISHED)
    draft_event = event_factory(status=EventStatus.DRAFT)
    
    url = reverse('events-list')

    # Аноним
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == pub_event.id

    # Обычный пользователь
    user = user_factory()
    api_client.force_authenticate(user=user)
    response = api_client.get(url)
    assert len(response.data['results']) == 1

    # Админ
    admin = user_factory(is_superuser=True)
    api_client.force_authenticate(user=admin)
    response = api_client.get(url)
    assert len(response.data['results']) == 2

@pytest.mark.django_db
def test_event_crud_superuser(api_client, user_factory, venue_factory):
    """Полный CRUD для админа (Создание, Чтение, Обновление, Удаление)"""
    admin = user_factory(is_superuser=True)
    venue = venue_factory()
    api_client.force_authenticate(user=admin)
    
    # 1. CREATE
    url_list = reverse('events-list')
    data = {
        "title": "Mega Party",
        "description": "Best party",
        "start_at": "2026-05-01T20:00:00Z",
        "end_at": "2026-05-01T23:00:00Z",
        "publish_at": "2026-04-01T12:00:00Z",
        "venue": venue.id,
        "status": "PUBLISHED"
    }
    response = api_client.post(url_list, data)
    assert response.status_code == 201
    event_id = response.data['id']
    
    # 2. RETRIEVE
    url_detail = reverse('events-detail', args=[event_id])
    response = api_client.get(url_detail)
    assert response.status_code == 200
    assert response.data['title'] == "Mega Party"
    
    # 3. UPDATE
    response = api_client.patch(url_detail, {"title": "Updated Party"})
    assert response.status_code == 200
    assert response.data['title'] == "Updated Party"
    
    # 4. DELETE
    response = api_client.delete(url_detail)
    assert response.status_code == 204
    
    # Проверка удаления (статус DELETED, так как у нас soft delete)
    from events.models import Event
    event = Event.objects.get(id=event_id)
    assert event.status == EventStatus.DELETED

@pytest.mark.django_db
def test_event_create_forbidden_for_user(api_client, user_factory, venue_factory):
    user = user_factory()
    venue = venue_factory()
    api_client.force_authenticate(user=user)
    
    url = reverse('events-list')
    data = {
        "title": "Hacked Event",
        "start_at": "2026-05-01T12:00:00Z",
        "end_at": "2026-05-01T13:00:00Z",
        "venue": venue.id
    }
    
    response = api_client.post(url, data)
    assert response.status_code == 403

@pytest.mark.django_db
def test_event_update_forbidden_for_user(api_client, user_factory, event_factory):
    event = event_factory(title="Original Title", status=EventStatus.PUBLISHED)
    user = user_factory()
    api_client.force_authenticate(user=user)
    
    url = reverse('events-detail', args=[event.id])
    response = api_client.patch(url, {"title": "Hacked Title"})
    assert response.status_code == 403
    
    event.refresh_from_db()
    assert event.title == "Original Title"

@pytest.mark.django_db
def test_event_delete_forbidden_for_user(api_client, user_factory, event_factory):
    event = event_factory(status=EventStatus.PUBLISHED)
    user = user_factory()
    api_client.force_authenticate(user=user)
    
    url = reverse('events-detail', args=[event.id])
    response = api_client.delete(url)
    assert response.status_code == 403

@pytest.mark.django_db
def test_get_weather_action(api_client, event_factory, mocker):
    mock_weather = mocker.patch('events.views.get_forecast_for_time')
    mock_weather.return_value = {
        "temperature_celsius": 25.0,
        "humidity_percent": 50,
        "pressure_mmhg": 760,
        "wind_speed_ms": 5.0,
        "wind_direction": 180
    }

    event = event_factory(status=EventStatus.PUBLISHED)
    
    url = reverse('events-get-weather', args=[event.id])
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response.data['temperature_celsius'] == 25.0
    mock_weather.assert_called_once()
