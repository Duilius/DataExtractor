// search.js

export function initializeSearch() {
    const searchByAreaBtn = document.getElementById('searchByArea');
    const searchByWorkerBtn = document.getElementById('searchByWorker');

    if (searchByAreaBtn) {
        searchByAreaBtn.addEventListener('click', openAreaSearch);
    }
    if (searchByWorkerBtn) {
        searchByWorkerBtn.addEventListener('click', openWorkerSearch);
    }
}

function openAreaSearch() {
    console.log("Abriendo búsqueda por área");
    openModal(areaSearchUrl);
}

function openWorkerSearch() {
    console.log("Abriendo búsqueda por trabajador");
    openModal(workerSearchUrl);
}

function openModal(contentUrl) {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modal-body');

    console.log("Abriendo modal con URL:", contentUrl);  // Añadir este log

    fetch(contentUrl)
        .then(response => {
            console.log("Respuesta recibida:", response.status);  // Añadir este log
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            console.log("Contenido HTML recibido");  // Añadir este log
            modalBody.innerHTML = html;
            modal.style.display = 'block';
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
        })
        .catch(error => {
            console.error('Error loading modal content:', error);
            modalBody.innerHTML = `<p>Error al cargar el contenido: ${error.message}</p>`;
            modal.style.display = 'block';
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
        });

    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.onclick = closeModal;
    }

    window.onclick = (event) => {
        if (event.target === modal) {
            closeModal();
        }
    };
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Asegúrate de que initializeSearch se llame cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', initializeSearch);


//IMPLEMENTACIÓN PARA MODAL BÚSQUEDA POR ÁREA/TRABAJADOR
document.addEventListener('DOMContentLoaded', () => {
    const areaSearch = document.getElementById('area-search');
    const showDependencies = document.getElementById('show-dependencies');
    const showSubDependencies = document.getElementById('show-sub-dependencies');
    /*
    areaSearch.addEventListener('input', () => {
        if (areaSearch.value.length >= 3) {
            searchAreas(areaSearch.value);
        }
    });
    */
    /*
    showDependencies.addEventListener('click', () => {
        const selectedArea = document.getElementById('selected-area').textContent;
        if (selectedArea !== 'Ninguna') {
            searchDependencies(selectedArea);
        }
    });
    */
    /*
    showSubDependencies.addEventListener('click', () => {
        const selectedSubArea = document.getElementById('selected-sub-area').textContent;
        if (selectedSubArea !== 'Ninguna') {
            searchSubDependencies(selectedSubArea);
        }
    });
    */
});

function searchAreas(query) {
    // Aquí iría la lógica para buscar áreas en la base de datos
    // Por ahora, simularemos con un resultado de ejemplo
    const results = ['Área 1', 'Área 2', 'Área 3'].filter(area => area.toLowerCase().includes(query.toLowerCase()));
    displayResults(results, 'area-results', selectArea);
}

function searchDependencies(area) {
    // Simular búsqueda de dependencias
    const results = ['Subárea 1', 'Subárea 2', 'Subárea 3'];
    displayResults(results, 'sub-area-results', selectSubArea);
}

function searchSubDependencies(subArea) {
    // Simular búsqueda de sub-dependencias
    const results = ['Sub-subárea 1', 'Sub-subárea 2', 'Sub-subárea 3'];
    displayResults(results, 'sub-sub-area-results', selectSubSubArea);
}

function displayResults(results, containerId, selectFunction) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    results.forEach(result => {
        const div = document.createElement('div');
        div.textContent = result;
        div.className = 'search-result-item';
        div.addEventListener('click', () => selectFunction(result));
        container.appendChild(div);
    });
}

function selectArea(area) {
    document.getElementById('selected-area').textContent = area;
    document.getElementById('show-dependencies').disabled = false;
}

function selectSubArea(subArea) {
    document.getElementById('selected-sub-area').textContent = subArea;
    document.getElementById('show-sub-dependencies').disabled = false;
}

function selectSubSubArea(subSubArea) {
    document.getElementById('selected-sub-sub-area').textContent = subSubArea;
    // Aquí podrías cargar los empleados de esta sub-sub-área
    loadEmployees(subSubArea);
}

function loadEmployees(area) {
    // Simular carga de empleados
    const employees = [
        { code: '001', name: 'Juan Pérez', image: 'path/to/image1.jpg' },
        { code: '002', name: 'María García', image: 'path/to/image2.jpg' },
        { code: '003', name: 'Carlos López', image: 'path/to/image3.jpg' },
    ];
    displayEmployees(employees);
}

function displayEmployees(employees) {
    const container = document.getElementById('employees-list');
    container.innerHTML = '';
    employees.forEach(employee => {
        const div = document.createElement('div');
        div.className = 'employee-card';
        div.innerHTML = `
            <img src="${employee.image}" alt="${employee.name}">
            <p>${employee.code}</p>
            <p>${employee.name}</p>
        `;
        div.addEventListener('click', () => selectEmployee(employee));
        container.appendChild(div);
    });
}

function selectEmployee(employee) {
    // Aquí iría la lógica para mostrar los datos del empleado en la pantalla principal
    console.log('Empleado seleccionado:', employee);
    // Cerrar el modal y actualizar la pantalla principal
    closeModal();
    updateMainScreen(employee);
}

function updateMainScreen(employee) {
    // Actualizar la pantalla principal con los datos del empleado
    // Esto dependerá de cómo esté estructurada tu pantalla principal
}


function showModal() {
    const modal = document.getElementById('modal');
    modal.style.display = 'block';

    // Inicializar HTMX en el contenido del modal
    htmx.process(document.getElementById('modal-content'));

    // Inicializar HyperScript en el contenido del modal
    eval(_hyperscript.init(document.getElementById('modal-content')));

    // Agregar funcionalidad para cerrar el modal
    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        }
    }

    // Cerrar el modal si se hace clic fuera de él
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}

// Función de búsqueda (si es necesaria)
//function searchAreas(query) {
    // Tu lógica de búsqueda aquí
//}