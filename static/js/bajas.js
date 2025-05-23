// Estado global
let currentState = {
    page: 1,
    pageSize: 10,
    isSearching: false
};

// Función para cargar datos iniciales
async function loadPageData(page) {
    try {
        const response = await fetch(`/dashboard/inventariador/bienes-bajas-2024/data?page=${page}&limit=${currentState.pageSize}`);
        if (!response.ok) throw new Error('Error al cargar datos');
        
        const html = await response.text();
        
        // Actualizar el contenido de la tabla
        document.getElementById('results-body').innerHTML = html;
        
        // Extraer el total para mostrar el contador
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const totalElement = tempDiv.querySelector('[data-total]');
        if (totalElement) {
            const total = totalElement.getAttribute('data-total');
            updateResultCounter(total);
        }
        
        currentState.page = page;
        currentState.isSearching = false;
        
        // Actualizar los botones
        updatePaginationButtons();
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Función para búsqueda
async function searchBienes(event) {
    if (event) event.preventDefault();
    
    const query = document.getElementById('search-input').value;
    if (!query) return;
    
    const filterSelect = document.getElementById('filter');
    const formData = new FormData();
    formData.append('filter', filterSelect.value);
    formData.append('query', query);
    formData.append('page', '1');
    formData.append('limit', currentState.pageSize.toString());

    try {
        const response = await fetch('/dashboard/inventariador/search-bienes-bajas', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Error en la búsqueda');
        
        const html = await response.text();
        document.getElementById('results-body').innerHTML = html;
        
        // Extraer el total de resultados
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const totalElement = tempDiv.querySelector('[data-total]');
        if (totalElement) {
            const total = totalElement.getAttribute('data-total');
            updateResultCounter(total);
        }
        
        currentState.page = 1;
        currentState.isSearching = true;
        
        // Actualizar los botones
        updatePaginationButtons();
        
    } catch (error) {
        console.error('Error en la búsqueda:', error);
    }
}

// Función para mostrar el modal
function showModal(codigoCp) {
    const row = document.querySelector(`tr[data-codigo="${codigoCp}"]`);
    if (!row) return;

    const cells = Array.from(row.cells);
    const bien = {
        inv_2023: cells[0].textContent.trim(),
        codigo_cp: cells[1].textContent.trim(),
        codigo_sbn: cells[2].textContent.trim(),
        denominacion: cells[3].textContent.trim(),
        marca: cells[4].textContent.trim(),
        modelo: cells[5].textContent.trim(),
        num_serie: cells[6].textContent.trim(),
        dependencia: cells[7].textContent.trim()
    };

    const modalContent = document.getElementById('modal-content');
    modalContent.innerHTML = `
        <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
                <strong class="text-gray-600">Denominación</strong>
                <p class="mt-1">${bien.denominacion}</p>
            </div>
            <div>
                <strong class="text-gray-600">Inventario 2023</strong>
                <p class="mt-1">${bien.inv_2023}</p>
            </div>
            <div>
                <strong class="text-gray-600">Código Patrimonial</strong>
                <p class="mt-1">${bien.codigo_cp}</p>
            </div>
            <div>
                <strong class="text-gray-600">Código SBN</strong>
                <p class="mt-1">${bien.codigo_sbn}</p>
            </div>
            <div>
                <strong class="text-gray-600">Marca</strong>
                <p class="mt-1">${bien.marca}</p>
            </div>
            <div>
                <strong class="text-gray-600">Modelo</strong>
                <p class="mt-1">${bien.modelo}</p>
            </div>
            <div>
                <strong class="text-gray-600">Número de Serie</strong>
                <p class="mt-1">${bien.num_serie}</p>
            </div>
            <div>
                <strong class="text-gray-600">Dependencia</strong>
                <p class="mt-1">${bien.dependencia}</p>
            </div>
        </div>
    `;
    
    document.getElementById('modal').classList.remove('hidden');
}

// Función para actualizar el contador de resultados
function updateResultCounter(total) {
    const counterElement = document.getElementById('results-count');
    if (counterElement) {
        counterElement.textContent = `Total: ${total} registro${total !== '1' ? 's' : ''}`;
    }
}

// Navegación
function loadNextPage() {
    if (currentState.isSearching) {
        const formData = new FormData();
        formData.append('filter', document.getElementById('filter').value);
        formData.append('query', document.getElementById('search-input').value);
        formData.append('page', (currentState.page + 1).toString());
        formData.append('limit', currentState.pageSize.toString());
        
        fetch('/dashboard/inventariador/search-bienes-bajas', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            document.getElementById('results-body').innerHTML = html;
            currentState.page++;
            updatePaginationButtons();
        });
    } else {
        loadPageData(currentState.page + 1);
    }
}

function loadPreviousPage() {
    if (currentState.page > 1) {
        if (currentState.isSearching) {
            const formData = new FormData();
            formData.append('filter', document.getElementById('filter').value);
            formData.append('query', document.getElementById('search-input').value);
            formData.append('page', (currentState.page - 1).toString());
            formData.append('limit', currentState.pageSize.toString());
            
            fetch('/dashboard/inventariador/search-bienes-bajas', {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(html => {
                document.getElementById('results-body').innerHTML = html;
                currentState.page--;
                updatePaginationButtons();
            });
        } else {
            loadPageData(currentState.page - 1);
        }
    }
}

// Función para actualizar botones de paginación
function updatePaginationButtons() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (!prevBtn || !nextBtn) return;
    
    // El botón anterior solo se habilita si no estamos en la primera página
    prevBtn.disabled = currentState.page <= 1;
    prevBtn.classList.toggle('opacity-50', currentState.page <= 1);
    
    // El botón siguiente se habilita si hay suficientes resultados
    const rows = document.querySelectorAll('#results-body tr');
    nextBtn.disabled = rows.length < currentState.pageSize;
    nextBtn.classList.toggle('opacity-50', rows.length < currentState.pageSize);
}

// Función para limpiar búsqueda
function clearSearch() {
    document.getElementById('search-input').value = '';
    currentState.isSearching = false;
    loadPageData(1);
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Cargar datos iniciales
    loadPageData(1);
    
    // Configurar event listeners
    const searchForm = document.querySelector('form');
    if (searchForm) {
        searchForm.addEventListener('submit', searchBienes);
    }
    
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchBienes(e);
            }
        });
    }
    
    // Event listener para cerrar modal con ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.getElementById('modal').classList.add('hidden');
        }
    });
});