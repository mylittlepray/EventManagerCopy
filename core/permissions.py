# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.conf import settings

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsSuperUserOrPublicReadIfAllowed(BasePermission):
    """
    Разрешает доступ всем на чтение (GET), если в настройках VENUES_PUBLIC_READ_ACCESS = True.
    Изменение (POST, PUT, DELETE) — только для суперюзера.
    Если настройка False — только суперюзер видит всё.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_superuser:
            return True

        public_access = getattr(settings, 'VENUES_PUBLIC_READ_ACCESS', False)

        if public_access and request.method in SAFE_METHODS:
            return True

        return False