# tests/test_filtering.py
import pytest
from django.urls import reverse
from events.models import EventStatus
from datetime import timedelta
from django.utils import timezone

@pytest.mark.django_db
def test_filter_events_by_date_range(api_client, event_factory):
    """
    Проверяем фильтрацию по диапазонам дат (start_at, end_at).
    """
    now = timezone.now()
    
    # Событие 1: Вчера
    e_yesterday = event_factory(start_at=now - timedelta(days=2), end_at=now - timedelta(days=1, hours=-2), status=EventStatus.PUBLISHED)
    # Событие 2: Завтра
    e_tomorrow = event_factory(start_at=now + timedelta(days=1), end_at=now + timedelta(days=2, hours=2),status=EventStatus.PUBLISHED)
    # Событие 3: Через месяц
    e_future = event_factory(start_at=now + timedelta(days=30), end_at=now + timedelta(days=30, hours=2),status=EventStatus.PUBLISHED)
    
    url = reverse('events-list')
    
    # start_at_after (Начало > Сегодня)
    # Должны найти e_tomorrow и e_future
    response = api_client.get(url, {'start_from': now.isoformat()})
    assert len(response.data['results']) == 2
    ids = [r['id'] for r in response.data['results']]
    assert e_tomorrow.id in ids and e_future.id in ids
    
    # start_at_before (Начало < Сегодня)
    # Должны найти e_yesterday
    response = api_client.get(url, {'start_to': now.isoformat()})
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == e_yesterday.id
    
    # end_at_after (Окончание > Через неделю)
    # Должны найти e_future
    next_week = now + timedelta(days=7)
    response = api_client.get(url, {'end_from': next_week.isoformat()})
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == e_future.id

@pytest.mark.django_db
def test_filter_events_by_rating(api_client, event_factory):
    """
    Проверяем фильтрацию по рейтингу (min, max).
    """
    e1 = event_factory(rating=5, status=EventStatus.PUBLISHED)
    e2 = event_factory(rating=25, status=EventStatus.PUBLISHED)
    e3 = event_factory(rating=10, status=EventStatus.PUBLISHED)
    
    url = reverse('events-list')
    
    response = api_client.get(url, {'rating_min': 10})
    assert len(response.data['results']) == 2
    
    response = api_client.get(url, {'rating_max': 6})
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == e1.id

@pytest.mark.django_db
def test_ordering_events_all_fields(api_client, event_factory):
    """
    Проверяем сортировку по title, start_at, end_at.
    """
    now = timezone.now()
    
    # e1: A, start=3, end=1
    e1 = event_factory(title="A_Event", start_at=now+timedelta(days=3), end_at=now+timedelta(days=3, hours=1), status=EventStatus.PUBLISHED)
    # e2: B, start=2, end=2
    e2 = event_factory(title="B_Event", start_at=now+timedelta(days=2), end_at=now+timedelta(days=2, hours=2), status=EventStatus.PUBLISHED)
    # e3: C, start=1, end=3
    e3 = event_factory(title="C_Event", start_at=now+timedelta(days=1), end_at=now+timedelta(days=1, hours=3), status=EventStatus.PUBLISHED)
    
    url = reverse('events-list')
    
    # По Title (A-Z)
    response = api_client.get(url, {'ordering': 'title'})
    res = response.data['results']
    assert res[0]['id'] == e1.id
    assert res[1]['id'] == e2.id
    assert res[2]['id'] == e3.id
    
    # По Title (Z-A)
    response = api_client.get(url, {'ordering': '-title'})
    res = response.data['results']
    assert res[0]['id'] == e3.id
    assert res[1]['id'] == e2.id
    assert res[2]['id'] == e1.id

    # По start_at (Раньше > Позже)
    # e3 (day+1) > e2 (day+2) > e1 (day+3)
    response = api_client.get(url, {'ordering': 'start_at'})
    res = response.data['results']
    assert res[0]['id'] == e3.id
    assert res[1]['id'] == e2.id
    assert res[2]['id'] == e1.id
    
    # 4. По end_at (Раньше > Позже)
    # Порядок: e3, e2, e1
    response = api_client.get(url, {'ordering': 'end_at'})
    res = response.data['results']
    assert res[0]['id'] == e3.id
    assert res[1]['id'] == e2.id
    assert res[2]['id'] == e1.id