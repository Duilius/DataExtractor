// Agregar al inicio del archivo
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebarToggle && sidebar && mainContent) {
        sidebarToggle.addEventListener('click', () => {
            console.log('Toggle clicked'); // Para debug
            sidebar.classList.toggle('sidebar-collapsed');
            mainContent.classList.toggle('main-content-expanded');
            
            // Guardar estado del menú
            const isCollapsed = sidebar.classList.contains('sidebar-collapsed');
            localStorage.setItem('sidebarState', isCollapsed ? 'collapsed' : 'expanded');
        });
    }
}

// Agregar a las funciones que se ejecutan en DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    initSidebarToggle();
    // resto del código existente
});

// Funciones globales para los dashboards
document.addEventListener('DOMContentLoaded', function() {
    // Manejar el logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Inicializar tooltips si existen
    initTooltips();

    // Inicializar contadores animados
    initCounters();
});

// Función para manejar el cierre de sesión
function handleLogout() {
    fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        window.location.href = '/auth/login';
    });
}

// Animación de contadores
function initCounters() {
    document.querySelectorAll('.metric-value').forEach(counter => {
        const target = parseInt(counter.innerText);
        if (!isNaN(target)) {
            let count = 0;
            const duration = 1000; // 1 segundo
            const step = target / (duration / 16); // 60 FPS
            
            const timer = setInterval(() => {
                count += step;
                if (count >= target) {
                    counter.innerText = target;
                    clearInterval(timer);
                } else {
                    counter.innerText = Math.floor(count);
                }
            }, 16);
        }
    });
}

// Inicializar tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', e => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = element.dataset.tooltip;
            document.body.appendChild(tooltip);
            
            const rect = element.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width/2) - (tooltip.offsetWidth/2)}px`;
        });
        
        element.addEventListener('mouseleave', () => {
            document.querySelectorAll('.tooltip').forEach(t => t.remove());
        });
    });
}

// Función para formatear números grandes
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

// Función para actualizar datos en tiempo real (si se implementa)
function updateMetrics() {
    fetch('/api/dashboard/metrics')
        .then(response => response.json())
        .then(data => {
            // Actualizar métricas específicas según el dashboard
            if (data.totalBienes) {
                document.getElementById('totalBienes').innerText = formatNumber(data.totalBienes);
            }
            if (data.avanceGlobal) {
                document.getElementById('avanceGlobal').innerText = `${data.avanceGlobal}%`;
            }
        })
        .catch(console.error);
}