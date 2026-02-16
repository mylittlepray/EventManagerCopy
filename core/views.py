from django.shortcuts import render

# Create your views here.
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView

from core.forms import SignUpForm

@extend_schema(responses={200: None})
class IndexView(TemplateView):
    template_name = "core/index.html"

class EventDetailView(TemplateView):
    template_name = "core/event_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_id'] = kwargs.get('pk')
        return context

class RegisterView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'