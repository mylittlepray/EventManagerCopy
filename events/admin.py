# events/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Event, EventImage, EmailNotificationConfig

# Inline позволяет добавлять картинки прямо на странице редактирования События
class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1 # Сколько пустых строк показывать
    readonly_fields = ('preview',) # Показываем превью загруженной картинки

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 50px;" />', obj.image.url)
        return "-"
    preview.short_description = "Превью"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'start_at', 'venue', 'author', 'preview_thumb')
    list_filter = ('status', 'start_at', 'venue')
    search_fields = ('title', 'description')
    
    fieldsets = (
        ("Основное", {
            "fields": ("title", "description", "status", "author")
        }),
        ("Даты и Место", {
            "fields": ("start_at", "end_at", "publish_at", "venue")
        }),
        ("Медиа и Рейтинг", {
            "fields": ("preview_image", "rating", "weather") 
        }),
    )
    
    readonly_fields = ('weather', 'preview_image')
    inlines = [EventImageInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def preview_thumb(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" style="height: 40px; border-radius: 4px;" />', obj.preview_image.url)
        return "Нет фото"
    preview_thumb.short_description = "Обложка"

@admin.register(EmailNotificationConfig)
class EmailNotificationConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not EmailNotificationConfig.objects.exists()
