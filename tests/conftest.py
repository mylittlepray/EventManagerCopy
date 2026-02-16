# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from pytest_factoryboy import register
from tests.factories import UserFactory, VenueFactory, EventFactory

register(UserFactory)
register(VenueFactory)
register(EventFactory)

@pytest.fixture
def api_client():
    return APIClient()
