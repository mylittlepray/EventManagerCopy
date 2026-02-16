from django.urls import path, include
from core.views import IndexView, EventDetailView

from core.views import RegisterView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event_detail'),

    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('accounts/', include('django.contrib.auth.urls')), 

]
