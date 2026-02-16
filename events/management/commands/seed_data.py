from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
import random
from datetime import timedelta
from venues.models import Venue
from events.models import Event, EventImage, EventStatus

User = get_user_model()
fake = Faker('ru_RU') 

class Command(BaseCommand):
    help = 'Заполняет БД тестовыми местами и событиями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--venues',
            type=int,
            default=10,
            help='Количество мест для создания'
        )
        parser.add_argument(
            '--events',
            type=int,
            default=50,
            help='Количество событий для создания'
        )

    def handle(self, *args, **options):
        venues_count = options['venues']
        events_count = options['events']

        try:
            author = User.objects.filter(is_superuser=True).first()
            if not author:
                self.stdout.write(
                    self.style.ERROR('Суперпользователь не найден! Создай через createsuperuser')
                )
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка поиска пользователя: {e}'))
            return

        self.stdout.write('Создаём места проведения...')
        venues = []
        
        city_coords = [
            (55.7558, 37.6173, 'Москва'),
            (59.9343, 30.3351, 'Санкт-Петербург'),
            (56.8389, 60.6057, 'Екатеринбург'),
            (55.0084, 82.9357, 'Новосибирск'),
            (43.1155, 131.8855, 'Владивосток'),
            (56.0105, 92.8525, 'Красноярск')
        ]

        for i in range(venues_count):
            city_data = random.choice(city_coords)
            lat = city_data[0] + random.uniform(-0.1, 0.1)
            lon = city_data[1] + random.uniform(-0.1, 0.1)
            
            venue = Venue.objects.create(
                name=f"{fake.company()} ({city_data[2]})",
                location=f'POINT({lon} {lat})'
            )
            venues.append(venue)
            
        self.stdout.write(self.style.SUCCESS(f'✓ Создано {venues_count} мест'))

        # 2. Создаём события
        self.stdout.write('Создаём события...')
        
        event_types = [
            'Концерт', 'Выставка', 'Конференция', 'Фестиваль',
            'Мастер-класс', 'Спектакль', 'Семинар', 'Воркшоп'
        ]
        
        for i in range(events_count):
            days_offset_start = random.randint(-60, 60)
            days_offset_end = days_offset_start + random.randint(1, 7)
            days_offset_publish = days_offset_start - random.randint(1, 14)
            
            start_datetime = timezone.now() + timedelta(days=days_offset_start, hours=random.randint(10, 20))
            end_datetime = start_datetime + timedelta(hours=random.randint(2, 8))
            publish_datetime = timezone.now() + timedelta(days=days_offset_publish)
            
            status = EventStatus.DRAFT if publish_datetime > timezone.now() else EventStatus.PUBLISHED
            
            event = Event.objects.create(
                title=f"{random.choice(event_types)}: {fake.catch_phrase()}",
                description=fake.text(max_nb_chars=500),
                publish_at=publish_datetime,
                start_at=start_datetime,
                end_at=end_datetime,
                author=author,
                venue=random.choice(venues),
                rating=random.randint(0, 25),
                status=status
            )
            
            for j in range(random.randint(1, 3)):
                EventImage.objects.create(
                    event=event,
                    image=f'events/test_image/test_image_{random.randint(1,10)}.jpg'
                )

        self.stdout.write(self.style.SUCCESS(f'✓ Создано {events_count} событий'))
        self.stdout.write(
            self.style.SUCCESS('Готово! Данные заполнены.')
        )
