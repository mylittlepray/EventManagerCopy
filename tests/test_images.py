# tests/test_images.py
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

def generate_image_file(name="test.jpg", size=(500, 500)):
    """Генерирует валидный JPG файл в памяти заданного размера"""
    file = BytesIO()
    image = Image.new('RGB', size, 'red')
    image.save(file, 'jpeg')
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type="image/jpeg")

@pytest.mark.django_db
def test_upload_multiple_images_and_preview_resize(api_client, user_factory, event_factory):
    """
    Проверяем загрузку нескольких файлов и корректность ресайза превью.
    """
    admin = user_factory(is_superuser=True)
    event = event_factory()
    api_client.force_authenticate(user=admin)
    
    url = reverse('events-images', args=[event.id])
    
    img1 = generate_image_file("img1.jpg", size=(800, 800))
    img2 = generate_image_file("img2.jpg", size=(1000, 600))
    
    data = {'images': [img1, img2]} 
    
    response = api_client.post(url, data, format='multipart')
    assert response.status_code == 201
    
    event.refresh_from_db()
    assert event.images.count() == 2
    
    assert event.preview_image
    
    with Image.open(event.preview_image) as img:
        width, height = img.size
        assert min(width, height) == 200