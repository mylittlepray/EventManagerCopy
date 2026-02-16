# events/services.py
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


def make_preview(image_field_file, min_side=200):
    """
    Делает превью: если картинка больше min_side по меньшей стороне — уменьшает так,
    чтобы меньшая сторона стала min_side. Если картинка уже маленькая — не увеличивает.
    Возвращает ContentFile (готово для event.preview_image.save()).
    """
    image_field_file.seek(0)
    img = Image.open(image_field_file)

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    w, h = img.size
    current_min = min(w, h)

    if current_min > min_side:
        scale = min_side / current_min
        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue())
