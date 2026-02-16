# venues/urls.py
from rest_framework.routers import DefaultRouter
from .views import VenueViewSet

router = DefaultRouter()
router.register(r"", VenueViewSet, basename="venues")

urlpatterns = router.urls
