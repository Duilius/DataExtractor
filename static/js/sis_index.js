// Variables globales para las gráficas
let activeCharts = {
    barChart: null,
    lineChart: null,
    pieChart: null,
    trendChart: null
};

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    setupTheme();
    initAllCharts();
    setupCityNavigation();
});

// Configuración del tema
function setupTheme() {
    const themeButton = document.querySelector('.theme-toggle');
    
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
        themeButton.textContent = '🌙';
    }

    themeButton.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        themeButton.textContent = isDark ? '🌙' : '☀️';
        
        destroyCharts();
        setTimeout(() => {
            initAllCharts();
        }, 50);
    });
}

// Configuración de colores para gráficas
const chartColors = {
    light: {
        primary: '#0066cc',
        secondary: ['#3399ff', '#66b3ff', '#99ccff'],
        text: '#333333',
        grid: '#e5e7eb'
    },
    dark: {
        primary: '#3399ff',
        secondary: ['#66b3ff', '#99ccff', '#cce6ff'],
        text: '#ffffff',
        grid: '#374151'
    }
};

// Destruir gráficas existentes
function destroyCharts() {
    Object.values(activeCharts).forEach(chart => {
        if (chart) {
            chart.destroy();
        }
    });
    activeCharts = {};
}

// Inicializar todas las gráficas
function initAllCharts() {
    const theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    const colors = chartColors[theme];

    Chart.defaults.color = colors.text;
    Chart.defaults.font.size = 11;
    
    // Configuración común
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 500
        }
    };

    // Gráfica de barras
    const barCtx = document.getElementById('barChart');
    if (barCtx) {
        activeCharts.barChart = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: ['Médicos', 'Mobiliario', 'IT'],
                datasets: [{
                    data: [300, 200, 100],
                    backgroundColor: colors.primary,
                    borderRadius: 4,
                    barPercentage: 0.3,
                    categoryPercentage: 0.7
                }]
            },
            options: {
                ...commonOptions,
                plugins: { 
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: colors.grid }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // Gráfica de línea
    const lineCtx = document.getElementById('lineChart');
    if (lineCtx) {
        activeCharts.lineChart = new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: ['Ene', 'Feb', 'Mar', 'Abr'],
                datasets: [{
                    data: [100, 250, 400, 500],
                    borderColor: colors.primary,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3
                }]
            },
            options: {
                ...commonOptions,
                plugins: { 
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: colors.grid }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // Gráfica de estado
    const pieCtx = document.getElementById('pieChart');
    if (pieCtx) {
        activeCharts.pieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Bueno', 'Regular', 'Malo'],
                datasets: [{
                    data: [70, 20, 10],
                    backgroundColor: [colors.primary, ...colors.secondary],
                    borderWidth: 0
                }]
            },
            options: {
                ...commonOptions,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 5,
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        });
    }

    // Gráfica de tendencia
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        activeCharts.trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: ['S1', 'S2', 'S3', 'S4'],
                datasets: [{
                    data: [100, 250, 200, 400],
                    borderColor: colors.primary,
                    tension: 0,
                    fill: false,
                    pointRadius: 4
                }]
            },
            options: {
                ...commonOptions,
                plugins: { 
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: colors.grid }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

// Navegación de ciudades
function setupCityNavigation() {
    const container = document.querySelector('.cities-scroll');
    const prevBtn = document.getElementById('prevCity');
    const nextBtn = document.getElementById('nextCity');
    let scrollPosition = 0;

    if (!container || !prevBtn || !nextBtn) return;

    function updateScroll() {
        container.style.transform = `translateX(-${scrollPosition}px)`;
        prevBtn.style.visibility = scrollPosition <= 0 ? 'hidden' : 'visible';
        nextBtn.style.visibility = 
            scrollPosition >= container.scrollWidth - container.parentElement.clientWidth 
            ? 'hidden' : 'visible';
    }

    prevBtn.addEventListener('click', () => {
        scrollPosition = Math.max(0, scrollPosition - 200);
        updateScroll();
    });

    nextBtn.addEventListener('click', () => {
        const maxScroll = container.scrollWidth - container.parentElement.clientWidth;
        scrollPosition = Math.min(maxScroll, scrollPosition + 200);
        updateScroll();
    });

    updateScroll();

    // Actualizar gráficas al seleccionar ciudad
    document.querySelectorAll('.city-pill').forEach(button => {
        button.addEventListener('click', async () => {
            try {
                const response = await fetch(`/api/stats/${button.textContent.toLowerCase()}`);
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();
                updateChartsData(data);
            } catch (error) {
                console.error('Error loading city data:', error);
            }
        });
    });
}

// Actualizar datos de las gráficas
function updateChartsData(data) {
    if (activeCharts.barChart && data.distribution) {
        activeCharts.barChart.data.datasets[0].data = data.distribution;
        activeCharts.barChart.update();
    }

    if (activeCharts.lineChart && data.processed) {
        activeCharts.lineChart.data.datasets[0].data = data.processed;
        activeCharts.lineChart.update();
    }

    if (activeCharts.pieChart && data.status) {
        activeCharts.pieChart.data.datasets[0].data = data.status;
        activeCharts.pieChart.update();
    }

    if (activeCharts.trendChart && data.trend) {
        activeCharts.trendChart.data.datasets[0].data = data.trend;
        activeCharts.trendChart.update();
    }
}