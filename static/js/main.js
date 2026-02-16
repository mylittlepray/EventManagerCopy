document.addEventListener('DOMContentLoaded', () => {
    loadVenues();
    loadEvents(); 

    document.getElementById('filterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        loadEvents(1); 
    });
});


async function loadVenues() {
    const select = document.getElementById('venueFilter');
    if (!select) return;

    try {
        const response = await fetch('/api/venues/'); 
        if (response.ok) {
            const data = await response.json();
            const venues = data.results || data; 
            
            venues.forEach(venue => {
                const option = document.createElement('option');
                option.value = venue.id;
                option.textContent = venue.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.warn('Не удалось загрузить список площадок:', error);
    }
}

/**
 * Основная функция загрузки событий
 * @param {number} page - номер страницы
 */
async function loadEvents(page = 1) {
    const container = document.getElementById('events-container');
    const paginationContainer = document.getElementById('pagination');
    
    container.innerHTML = `
        <div class="col-12 loading-overlay">
            <div class="spinner-border text-primary" role="status"></div>
        </div>
    `;
    paginationContainer.innerHTML = '';

    const params = new URLSearchParams();
    params.append('page', page);

    const getValue = (id) => document.getElementById(id)?.value;
    
    const search = getValue('search');
    if (search) params.append('search', search);

    const ordering = getValue('ordering');
    if (ordering) params.append('ordering', ordering);

    const startAfter = getValue('start_at_after');
    if (startAfter) params.append('start_at_after', startAfter);
    const startBefore = getValue('start_at_before');
    if (startBefore) params.append('start_at_before', startBefore);

    const endAfter = getValue('end_at_after');
    if (endAfter) params.append('end_at_after', endAfter);
    const endBefore = getValue('end_at_before');
    if (endBefore) params.append('end_at_before', endBefore);

    const ratingMin = getValue('rating_min');
    if (ratingMin) params.append('rating_min', ratingMin);
    const ratingMax = getValue('rating_max');
    if (ratingMax) params.append('rating_max', ratingMax);

    const venueSelect = document.getElementById('venueFilter');
    if (venueSelect) {
        const selectedVenues = Array.from(venueSelect.selectedOptions).map(opt => opt.value);
        selectedVenues.forEach(id => params.append('venue', id));
    }

    try {
        const response = await fetch(`/api/events/?${params.toString()}`);
        if (!response.ok) throw new Error('Ошибка API');
        
        const data = await response.json();
        renderEvents(data.results, container);
        renderPagination(data, page, paginationContainer);
        
    } catch (error) {
        console.error(error);
        container.innerHTML = '<div class="alert alert-danger w-100">Ошибка загрузки событий. Проверьте API.</div>';
    }
}

function renderEvents(events, container) {
    container.innerHTML = '';
    
    if (!events || events.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted py-5"><h4>Событий не найдено 😔</h4></div>';
        return;
    }

    events.forEach(event => {
        const options = { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' };
        const start = new Date(event.start_at).toLocaleDateString('ru-RU', options);
        
        const shortDesc = event.description ? 
            (event.description.length > 100 ? event.description.substring(0, 100) + '...' : event.description) 
            : 'Описание отсутствует';

        const imageSrc = event.preview_image || 'https://via.placeholder.com/400x250?text=No+Image';

        const html = `
            <div class="col">
                <div class="card h-100 event-card shadow-sm">
                    <div style="position: relative;">
                        <img src="${imageSrc}" class="card-img-top" alt="${event.title}">
                        <div class="badge-rating">★ ${event.rating || 0}</div>
                    </div>
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title text-primary">${event.title}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">
                            <i class="bi bi-calendar-event"></i> ${start}
                        </h6>
                        <p class="card-text flex-grow-1">${shortDesc}</p>
                        <div class="d-grid mt-3">
                            <a href="/events/${event.id}/" class="btn btn-outline-primary">Подробнее</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    });
}

function renderPagination(data, currentPage, container) {
    if (!data.next && !data.previous) return;

    let html = '<ul class="pagination justify-content-center">';
    
    if (data.previous) {
        html += `<li class="page-item"><button class="page-link" onclick="loadEvents(${currentPage - 1})">← Назад</button></li>`;
    } else {
        html += `<li class="page-item disabled"><span class="page-link">← Назад</span></li>`;
    }

    html += `<li class="page-item active"><span class="page-link">${currentPage}</span></li>`;

    if (data.next) {
        html += `<li class="page-item"><button class="page-link" onclick="loadEvents(${currentPage + 1})">Вперед →</button></li>`;
    } else {
        html += `<li class="page-item disabled"><span class="page-link">Вперед →</span></li>`;
    }

    html += '</ul>';
    container.innerHTML = html;
}
