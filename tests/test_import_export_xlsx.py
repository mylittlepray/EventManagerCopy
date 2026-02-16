# tests/test_import_export_xlsx.py
import pytest
import openpyxl
from django.urls import reverse
from io import BytesIO

from events.models import EventStatus

@pytest.mark.django_db
def test_import_xlsx_success(api_client, user_factory, venue_factory):
    admin = user_factory(is_superuser=True)
    venue = venue_factory(name="Test Venue")
    api_client.force_authenticate(user=admin)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["title", "description", "publish_at", "start_at", "end_at", "venue_name", "coords", "rating"])
    ws.append(["Imported Party", "Desc", "", "2026-01-01 10:00:00", "2026-01-01 12:00:00", "Test Venue", "37.61, 55.75", 5]) 
    
    file_obj = BytesIO()
    wb.save(file_obj)
    file_obj.seek(0)
    file_obj.name = "events.xlsx"
    
    url = reverse('events-import-xlsx')
    
    data = {"file": file_obj}
    response = api_client.post(url, data, format='multipart')

    assert response.status_code == 201
    assert "Successfully imported 1 events" in response.data['message']

@pytest.mark.django_db
def test_import_xlsx_bad_file(api_client, user_factory):
    admin = user_factory(is_superuser=True)
    api_client.force_authenticate(user=admin)
    
    file_obj = BytesIO(b"Not an excel file")
    file_obj.name = "bad.txt"
    
    url = reverse('events-import-xlsx')
    response = api_client.post(url, {"file": file_obj}, format='multipart')
    
    assert response.status_code == 400

@pytest.mark.django_db
def test_export_xlsx(api_client, event_factory):
    event_factory.create_batch(5, status=EventStatus.PUBLISHED)
    
    url = reverse('events-export-xlsx')
    
    response = api_client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    file_content = BytesIO(response.content)
    wb = openpyxl.load_workbook(file_content)
    ws = wb.active
    
    rows = list(ws.rows)
    assert len(rows) == 6 
    assert rows[0][0].value == "Дата публикации" 
