document.addEventListener('DOMContentLoaded', () => {
    // Проверка, передан ли ID (он объявляется глобально в шаблоне)
    if (window.eventId) {
        initEventPage(window.eventId);
    }
});

// Глобальный массив для хранения списка картинок (чтобы не дублировать слайды)
let allSlides = [];

/**
 * Оркестратор загрузки страницы
 */
async function initEventPage(id) {
    const container = document.getElementById('event-detail-content');
    
    // 1. Сначала грузим основную инфу (критично для отображения)
    try {
        const response = await fetch(`/api/events/${id}/`);
        if (response.status === 404) {
            container.innerHTML = '<div class="alert alert-warning text-center mt-5">Событие не найдено или скрыто.</div>';
            return;
        }
        if (!response.ok) throw new Error('Ошибка API');
        
        const event = await response.json();
        
        // Рендерим скелет и основную инфу
        renderMainInfo(event);
        showContent(); // Показываем верстку пользователю

        // 2. Параллельно догружаем "тяжелые" данные (не блокируя интерфейс)
        loadAdditionalData(id);

    } catch (error) {
        console.error(error);
        container.innerHTML = '<div class="alert alert-danger text-center mt-5">Не удалось загрузить событие.</div>';
    }
}

/**
 * Рендер основной информации (Title, Description, Venue) + Первый слайд
 */
function renderMainInfo(event) {
    // Заголовки
    document.title = `${event.title} - EventManager`;
    document.getElementById('event-title').textContent = event.title;
    document.getElementById('event-description').innerHTML = event.description ? event.description.replace(/\n/g, '<br>') : '';
    
    // Даты
    const options = { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' };
    document.getElementById('event-start').textContent = new Date(event.start_at).toLocaleString('ru-RU', options);
    document.getElementById('event-end').textContent = new Date(event.end_at).toLocaleString('ru-RU', options);
    
    // Рейтинг
    const ratingEl = document.getElementById('event-rating');
    if (ratingEl) ratingEl.textContent = event.rating;

    // Локация
    if (event.venue) {
        const venueNameEl = document.getElementById('venue-name');
        if (venueNameEl) venueNameEl.textContent = event.venue.name;
        
        const venueCoordsEl = document.getElementById('venue-coords');
        if (venueCoordsEl && event.venue.location) {
            const { latitude, longitude } = event.venue.location;
            venueCoordsEl.href = `https://yandex.ru/maps/?pt=${longitude},${latitude}&z=15&l=map`;
        }
    }

    // --- ИНИЦИАЛИЗАЦИЯ ГАЛЕРЕИ (Только превью) ---
    allSlides = []; // Сброс глобального массива
    const previewUrl = event.preview_image || 'https://via.placeholder.com/800x400?text=Нет+изображения';
    
    // Добавляем превью как первый и активный слайд
    addSlide(previewUrl, true);
    
    // Показываем карусель, скрываем лоадер внутри неё
    const loader = document.getElementById('gallery-loader');
    if (loader) loader.classList.add('d-none');
    
    const carousel = document.getElementById('mainCarousel');
    if (carousel) carousel.classList.remove('d-none');
}

/**
 * Асинхронная дозагрузка Погоды и Картинкок
 */
async function loadAdditionalData(id) {
    // Используем allSettled, чтобы ошибка в одном запросе не ломала другой
    const [weatherResult, imagesResult] = await Promise.allSettled([
        fetch(`/api/events/${id}/weather/`),
        fetch(`/api/events/${id}/images/`)
    ]);

    // Обработка Погоды
    if (weatherResult.status === 'fulfilled' && weatherResult.value.ok) {
        const weatherData = await weatherResult.value.json();
        renderWeather(weatherData);
    }

    // Обработка Дополнительных Изображений
    if (imagesResult.status === 'fulfilled' && imagesResult.value.ok) {
    const imagesData = await imagesResult.value.json();

    // - пагинация: {count, next, previous, results:[...]}
    // - либо EventImagesResponse: {preview_image_url, images:[...]} [file:1]
    const imagesList = imagesData.results || imagesData.images || [];

    if (imagesList.length > 0) {
        // КЛЮЧЕВОЕ: если есть реальные фото — убираем превью и пересобираем карусель
        resetCarousel();

        imagesList.forEach((imgObj, idx) => {
        const url = imgObj.image || imgObj;
        addSlide(url, idx === 0); // первый слайд активный
        });

        updateCarouselControls();
        }
    }
}

/**
 * Хелпер: Добавить слайд в DOM
 */
function addSlide(imageUrl, isActive) {
    const inner = document.getElementById('carousel-inner');
    const indicators = document.getElementById('carousel-indicators');
    
    if (!inner || !indicators) return;

    const slideIndex = allSlides.length;

    // 1. Создаем сам слайд
    const item = document.createElement('div');
    item.className = `carousel-item ${isActive ? 'active' : ''}`;
    // Стили: высота 400px, картинка центрируется, фон серый (если картинка не во весь размер)
    item.innerHTML = `
        <img src="${imageUrl}" class="d-block w-100" style="height: 400px; object-fit: contain; background-color: #f8f9fa;" alt="Слайд ${slideIndex + 1}">
    `;
    inner.appendChild(item);

    // 2. Создаем индикатор (нижняя черточка)
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.bsTarget = '#mainCarousel';
    btn.dataset.bsSlideTo = slideIndex;
    if (isActive) {
        btn.className = 'active';
        btn.ariaCurrent = 'true';
    }
    btn.ariaLabel = `Slide ${slideIndex + 1}`;
    indicators.appendChild(btn);

    // Запоминаем, что добавили
    allSlides.push(imageUrl);
}

function resetCarousel() {
  allSlides = [];

  const inner = document.getElementById('carousel-inner');
  const indicators = document.getElementById('carousel-indicators');

  if (inner) inner.innerHTML = '';
  if (indicators) indicators.innerHTML = '';

  // На всякий случай прячем стрелки до тех пор, пока не будет >1 слайда
  const prevBtn = document.getElementById('btn-prev');
  const nextBtn = document.getElementById('btn-next');
  if (prevBtn) prevBtn.classList.add('d-none');
  if (nextBtn) nextBtn.classList.add('d-none');
}


/**
 * Хелпер: Показать стрелки навигации, если слайдов > 1
 */
function updateCarouselControls() {
    if (allSlides.length > 1) {
        const prevBtn = document.getElementById('btn-prev');
        const nextBtn = document.getElementById('btn-next');
        if (prevBtn) prevBtn.classList.remove('d-none');
        if (nextBtn) nextBtn.classList.remove('d-none');
    }
}

/**
 * Хелпер: Отрисовка погоды
 */
function renderWeather(weather) {
    if (!weather) return;

    const tempEl = document.getElementById('weather-temp');
    if (tempEl) tempEl.textContent = weather.temperature_celsius > 0 ? `+${weather.temperature_celsius}` : weather.temperature_celsius;
    
    const humEl = document.getElementById('weather-humidity');
    if (humEl) humEl.textContent = weather.humidity_percent;
    
    const windEl = document.getElementById('weather-wind');
    if (windEl) windEl.textContent = weather.wind_speed_ms;
    
    const pressEl = document.getElementById('weather-pressure');
    if (pressEl) pressEl.textContent = weather.pressure_mmhg;
    
    const noteEl = document.getElementById('weather-note');
    if (noteEl) {
        const createdDate = new Date(weather.created_at).toLocaleString('ru-RU');
        noteEl.textContent = `* Прогноз на момент начала события (актуализирован: ${createdDate})`;
    }

    const weatherBlock = document.getElementById('weather-block');
    if (weatherBlock) weatherBlock.classList.remove('d-none');
}

/**
 * Хелпер: Переключение с лоадера на основной контент
 */
function showContent() {
    const loader = document.getElementById('event-detail-content');
    const layout = document.getElementById('main-layout');
    
    if (loader) loader.classList.add('d-none');
    if (layout) layout.classList.remove('d-none');
}
