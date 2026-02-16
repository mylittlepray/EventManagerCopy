# tests/factories.py
import factory
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from events.models import Event, EventStatus
from venues.models import Venue
from datetime import timedelta, timezone

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True
    
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    is_staff = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password("password123")

class VenueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Venue
    
    name = factory.Faker("company")
    location = Point(37.6173, 55.7558) 

class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event
    
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text")
    start_at = factory.Faker("future_datetime", tzinfo=timezone.utc)
    end_at = factory.LazyAttribute(lambda o: o.start_at + timedelta(hours=2))
    publish_at = factory.LazyAttribute(lambda o: o.start_at - timedelta(days=1))
    status = EventStatus.PUBLISHED
    venue = factory.SubFactory(VenueFactory)
    author = factory.SubFactory(UserFactory)
