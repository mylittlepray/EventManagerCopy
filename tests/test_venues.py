# tests/test_venues.py
import pytest
from django.urls import reverse
from django.test import override_settings

from venues.models import Venue

@override_settings(VENUES_PUBLIC_READ_ACCESS=False) 
@pytest.mark.django_db
def test_venue_list_permissions(api_client, venue_factory, user_factory):
    """
    Проверяем права доступа к списку площадок.
    Обычным пользователям просмотр запрещен.
    """
    venue_factory.create_batch(3)
    url = reverse('venues-list')

    # Аноним 
    response = api_client.get(url)
    assert response.status_code == 403

    # Обычный пользователь
    user = user_factory()
    api_client.force_authenticate(user=user)
    response = api_client.get(url)
    assert response.status_code == 403

    # Админ
    admin = user_factory(is_superuser=True, is_staff=True)
    api_client.force_authenticate(user=admin)
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data['results']) == 3

@pytest.mark.django_db
def test_venue_crud_superuser(api_client, user_factory, venue_factory):
    """
    Полный цикл CRUD для админа: Create, Retrieve, Update, Delete.
    """
    admin = user_factory(is_superuser=True, is_staff=True)
    api_client.force_authenticate(user=admin)

    # 1. CREATE
    url_list = reverse('venues-list')
    data = {"name": "New Arena", "location": "POINT(30 60)"}
    response = api_client.post(url_list, data)
    assert response.status_code == 201
    venue_id = response.data['id']

    # 2. RETRIEVE
    url_detail = reverse('venues-detail', args=[venue_id])
    response = api_client.get(url_detail)
    assert response.status_code == 200
    assert response.data['name'] == "New Arena"

    # 3. UPDATE (PUT)
    update_data = {"name": "Updated Arena", "location": "POINT(31 61)"}
    response = api_client.put(url_detail, update_data)
    assert response.status_code == 200
    assert response.data['name'] == "Updated Arena"

    # 4. DESTROY
    response = api_client.delete(url_detail)
    assert response.status_code == 204
    
    # Проверка, что удалилось
    assert not Venue.objects.filter(id=venue_id).exists()
    response = api_client.get(url_detail)
    assert response.status_code == 404

@pytest.mark.django_db
def test_venue_update_forbidden_for_user(api_client, user_factory, venue_factory):
    """Обычный юзер не может менять площадки"""
    venue = venue_factory(name="Old Name")
    user = user_factory()
    api_client.force_authenticate(user=user)
    
    url = reverse('venues-detail', args=[venue.id])
    data = {"name": "Hacked Name", "location": "POINT(0 0)"}
    
    response = api_client.put(url, data)
    assert response.status_code == 403
    
    venue.refresh_from_db()
    assert venue.name == "Old Name"

@pytest.mark.django_db
def test_venue_delete_forbidden_for_user(api_client, user_factory, venue_factory):
    """Обычный юзер не может удалять площадки"""
    venue = venue_factory(name="To be deleted")
    user = user_factory()
    api_client.force_authenticate(user=user)
    
    url = reverse('venues-detail', args=[venue.id])
    
    response = api_client.delete(url)
    assert response.status_code == 403
    
    assert Venue.objects.filter(id=venue.id).exists()