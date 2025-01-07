// Estado global
let currentState = {
    page: 1,
    pageSize: 10,
    selectedSede: null,
    searchQuery: ''
};

// Función para cargar empleados
async function cargarEmpleados(sedeId, page = 1) {
    if (!sedeId) return;
    
    // Guardar el valor del select en el estado
    currentState.selectedSede = sedeId;
    currentState.page = page;
    
    try {
        let url = `/dashboard/inventariador/sede-empleado/empleados/${sedeId}?page=${page}`;
        if (currentState.searchQuery) {
            url += `&query=${encodeURIComponent(currentState.searchQuery)}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Error al cargar empleados');
        
        const html = await response.text();
        
        // Actualizar tabla
        document.getElementById('empleados-body').innerHTML = html;
        
        // Extraer y mostrar total
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const totalElement = tempDiv.querySelector('[data-total]');
        if (totalElement) {
            const total = totalElement.getAttribute('data-total');
            updateResultCounter(total);
        }
        
        // Mostrar contenedor si está oculto
        const container = document.getElementById('empleados-container');
        container.classList.remove('collapsed');
        document.getElementById('toggle-icon').className = 'ri-arrow-up-s-line text-2xl';
        
        // Actualizar botones
        updatePaginationButtons();
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Función para buscar empleados
function buscarEmpleados() {
    const query = document.getElementById('search-input').value;
    currentState.searchQuery = query;
    if (currentState.selectedSede) {
        cargarEmpleados(currentState.selectedSede, 1);
    }
}

// Función para seleccionar empleado
function seleccionarEmpleado(empleadoId) {
    // Actualizar el iframe
    const iframe = document.getElementById('ficha-frame');
    iframe.src = `/dashboard/gerencia/fichaLevInf/${empleadoId}`;
    
    // Minimizar el contenedor después de un breve delay
    setTimeout(() => {
        const container = document.getElementById('empleados-container');
        const icon = document.getElementById('toggle-icon');
        
        container.classList.add('collapsed');
        icon.classList.add('rotated');
    }, 300); // 300ms de delay
}

// Funciones de paginación
function loadNextPage() {
    if (currentState.selectedSede) {
        cargarEmpleados(currentState.selectedSede, currentState.page + 1);
    }
}

function loadPreviousPage() {
    if (currentState.page > 1 && currentState.selectedSede) {
        cargarEmpleados(currentState.selectedSede, currentState.page - 1);
    }
}

// Función para actualizar contador
function updateResultCounter(total) {
    const counterElement = document.getElementById('results-count');
    if (counterElement) {
        counterElement.textContent = `Total: ${total} empleado${total !== '1' ? 's' : ''}`;
    }
}

// Función para actualizar botones de paginación
function updatePaginationButtons() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (!prevBtn || !nextBtn) return;
    
    prevBtn.disabled = currentState.page <= 1;
    prevBtn.classList.toggle('opacity-50', currentState.page <= 1);
    
    const rows = document.querySelectorAll('#empleados-body tr');
    nextBtn.disabled = rows.length < currentState.pageSize;
    nextBtn.classList.toggle('opacity-50', rows.length < currentState.pageSize);
}

// Función para mostrar/ocultar empleados
function toggleEmpleados() {
    const container = document.getElementById('empleados-container');
    const icon = document.getElementById('toggle-icon');
    
    container.classList.toggle('collapsed');
    icon.classList.toggle('rotated');
}

// Event listener para búsqueda con Enter
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                buscarEmpleados();
            }
        });
    }
});

// PARA MEJORAR ESTILO DEL SELECT de Sedes
// Funciones para el select personalizado
function toggleSedeSelect() {
    const options = document.getElementById('sede-options');
    options.classList.toggle('show');
}

function selectSede(sedeId, element) {
    const headerText = document.getElementById('selected-sede-text');
    headerText.innerHTML = element.innerHTML;
    toggleSedeSelect();
    cargarEmpleados(sedeId);
}

// Cerrar el select al hacer clic fuera
document.addEventListener('click', function(event) {
    const container = document.querySelector('.custom-select-container');
    const options = document.getElementById('sede-options');
    
    if (!container.contains(event.target)) {
        options.classList.remove('show');
    }
});