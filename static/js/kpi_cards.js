// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {

    console.log(document.getElementById('total-bienes')); // Debería mostrar el elemento en la consola si existe.
    console.log(document.getElementById('estado-chart'));
    console.log(document.getElementById('tipo-chart'));
    console.log(document.getElementById('total-faltantes'));
    console.log(document.getElementById('total-pendientes'));
    // Configuración de colores para gráficos
    const chartColors = {
        estado: ['#4caf50', '#2196f3', '#ff9800', '#f44336', '#9c27b0', '#795548'],
        tipo: ['#4a90e2', '#f44336']
    };

    // Inicializar los gráficos
    let estadoChart = null;
    let tipoChart = null;

    // Función para actualizar todos los KPIs
    async function updateAllKPIs() {
        try {
            const response = await fetch('/dashboard/kpis');
            const data = await response.json();
            updateKPIDisplays(data);
        } catch (error) {
            console.error('Error al actualizar KPIs:', error);
        }
    }

    // Función para actualizar un KPI específico
    async function updateSingleKPI(kpiType) {
        const btn = document.querySelector(`[data-kpi="${kpiType}"]`);
        btn.classList.add('spinning');
        
        try {
            const response = await fetch('/dashboard/kpis');
            const data = await response.json();
            
            switch(kpiType) {
                case 'total':
                    updateTotalBienes(data.total_bienes);
                    break;
                case 'estado':
                    updateEstadoChart(data.distribucion_estado);
                    break;
                case 'tipo':
                    updateTipoChart(data.distribucion_tipo);
                    break;
                case 'faltantes':
                    updateFaltantes(data.faltantes);
                    break;
                case 'pendientes':
                    updatePendientes(data.asignaciones_pendientes);
                    break;
            }
        } catch (error) {
            console.error(`Error al actualizar ${kpiType}:`, error);
        } finally {
            btn.classList.remove('spinning');
        }
    }

    // Función para actualizar las visualizaciones de los KPIs
    function updateKPIDisplays(data) {
        updateTotalBienes(data.total_bienes);
        updateEstadoChart(data.distribucion_estado);
        updateTipoChart(data.distribucion_tipo);
        updateFaltantes(data.faltantes);
        updatePendientes(data.asignaciones_pendientes);
        updateLatestItem();
    }

    // Funciones para actualizar cada KPI específico
    function updateTotalBienes(total) {
        const totalElement = document.getElementById('total-bienes');
        if (totalElement) {
            totalElement.textContent = total || 0;
        } else {
            console.warn("Elemento 'total-bienes' no encontrado en el DOM.");
        }
    }

    function updateEstadoChart(data) {
        const ctx = document.getElementById('estado-chart');
        if (ctx) {
            if (estadoChart) {
                estadoChart.destroy();
            }
            estadoChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.map(item => item.estado),
                    datasets: [{
                        data: data.map(item => item.cantidad),
                        backgroundColor: chartColors.estado,
                    }]
                },
                options: { 
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#afafaf',  // Cambia 'white' al color que desees para la leyenda
                                font: {
                                    size: 14         // Puedes ajustar el tamaño de la fuente si es necesario
                                }
                            }
                        }
                    }
                }
            });
        } else {
            console.warn("Elemento 'estado-chart' no encontrado en el DOM.");
        }
    }

    function updateTipoChart(data) {
        const ctx = document.getElementById('tipo-chart');
        if (ctx) {
            if (tipoChart) {
                tipoChart.destroy();
            }
            tipoChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.map(item => item.tipo),
                    datasets: [{
                        data: data.map(item => item.cantidad),
                        backgroundColor: chartColors.tipo,
                    }]
                },
                options: { 
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#afafaf',  // Cambia 'white' al color que desees para la leyenda
                                font: {
                                    size: 14         // Puedes ajustar el tamaño de la fuente si es necesario
                                }
                            }
                        }
                    }
                }
            });
        } else {
            console.warn("Elemento 'tipo-chart' no encontrado en el DOM.");
        }
    }

    function updateFaltantes(faltantes) {
        const faltantesElement = document.getElementById('total-faltantes');
        if (faltantesElement) {
            faltantesElement.textContent = faltantes || 0;
        } else {
            console.warn("Elemento 'total-faltantes' no encontrado en el DOM.");
        }
    }

    function updatePendientes(pendientes) {
        const pendientesElement = document.getElementById('total-pendientes');
        if (pendientesElement) {
            pendientesElement.textContent = pendientes || 0;
        } else {
            console.warn("Elemento 'total-pendientes' no encontrado en el DOM.");
        }
    }

    // Evento de recarga para cada botón
    document.querySelectorAll('.refresh-btn').forEach(button => {
        button.addEventListener('click', function() {
            const kpiType = button.getAttribute('data-kpi');
            updateSingleKPI(kpiType);
        });
    });


    // ÚLTIMO BIEN INVENTARIADO * * * * * ÚLTIMO BIEN INVENTARIADO \\

    async function updateLatestItem() {
        try {
            const response = await fetch('/dashboard/latest-item');
            const data = await response.json();
            
            // Configurar imagen principal del bien
            const mainImage = document.getElementById('main-image');
            const defaultImage = '/static/img/inventario_equipos-7.webp';
            
            // Usar directamente la URL presignada
            mainImage.src = data.main_image || defaultImage;
            
            // Configurar miniaturas del bien
            const thumbnailContainer = document.querySelector('.thumbnail-container');
            thumbnailContainer.innerHTML = '';
            
            data.images.forEach(imageData => {
                const thumbnail = document.createElement('img');
                thumbnail.src = imageData.url || defaultImage;
                thumbnail.classList.add('thumbnail');
                thumbnail.alt = `Miniatura ${imageData.tipo}`;
                
                thumbnail.onclick = () => {
                    mainImage.classList.add('fade-out');
                    setTimeout(() => {
                        mainImage.src = thumbnail.src;
                        mainImage.classList.remove('fade-out');
                    }, 200);
                };
                
                thumbnailContainer.appendChild(thumbnail);
            });
            
            // Resto de la configuración del dashboard
            const custodianPhoto = document.getElementById('custodian-photo');
            custodianPhoto.src = "/static/img/" + (data.custodian.foto || 'default.png');
            
            document.getElementById('custodian-name').textContent = data.custodian.nombre || 'Sin asignar';
            document.getElementById('item-description').textContent = data.item.descripcion || 'Sin descripción';
            document.getElementById('item-brand').textContent = data.item.marca || 'Sin marca';
            document.getElementById('item-model').textContent = data.item.modelo || 'Sin modelo';
            document.getElementById('item-status').textContent = data.item.estado || 'Sin estado';
            document.getElementById('item-code').textContent = data.item.codigo_patrimonial || 'Sin código';
            document.getElementById('item-area').textContent = data.item.area || 'Sin área';
            
        } catch (error) {
            console.error("Error al actualizar el último bien inventariado:", error);
            alert("Hubo un error al cargar los datos del último bien inventariado");
        }
    }
    
    

// Llamar a la función al cargar la página
document.addEventListener('DOMContentLoaded', updateLatestItem);

//SELECTOR DE MINIATURAS
function selectImage(imageSrc) {
    const mainImage = document.getElementById('main-image');
    mainImage.style.opacity = '0'; // Desvanece la imagen actual

    // Cambia la imagen después de un pequeño retraso para el efecto de suavidad
    setTimeout(() => {
        mainImage.src = imageSrc;
        mainImage.style.opacity = '1'; // Aparece la nueva imagen
    }, 200); // Espera 200ms antes de cambiar la imagen
}



    // Cargar los KPIs al iniciar la página
    updateAllKPIs();
});
