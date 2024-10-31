// processor.js
import { speak, mostrarMensajeModal } from './utils.js';

export async function procesarCodigoBarras(imageData) {
    try {
        mostrarMensajeModal('Procesando imagen...', false);
        speak('Procesando imagen');

        const response = await fetch(imageData);
        const blob = await response.blob();
        
        const formData = new FormData();
        formData.append('file', blob, 'captura.jpg');

        const respuesta = await fetch('/procesar_codigo_barras', {
            method: 'POST',
            body: formData
        });

        if (!respuesta.ok) {
            throw new Error(`Error HTTP: ${respuesta.status}`);
        }
        
        const datos = await respuesta.json();
        
        if (datos.success) {
            const numCodigos = datos.resultados.length;
            const mensaje = `Se ${numCodigos === 1 ? 'ha' : 'han'} detectado ${numCodigos} código${numCodigos !== 1 ? 's' : ''} de barras`;
            mostrarMensajeModal(mensaje, false);
            speak(mensaje);
            mostrarResultados(datos);
            return true;
        } else {
            const mensaje = "No se detectaron códigos de barras";
            mostrarMensajeModal(mensaje, true);
            speak(mensaje);
            limpiarResultados();
            mostrarSugerencias();
            return false;
        }
        
    } catch (error) {
        console.error('Error:', error);
        const mensaje = "Error al procesar la imagen";
        mostrarMensajeModal(mensaje, true);
        speak(mensaje);
        limpiarResultados();
        return false;
    }
}

function mostrarResultados(datos) {
    const resultadosDiv = document.getElementById('resultados');
    if (!resultadosDiv) return;
    
    let html = '<div class="resultados-container">';
    
    if (datos.imagen_procesada) {
        html += `
            <div class="imagen-procesada-container">
                <img src="data:image/jpeg;base64,${datos.imagen_procesada}" 
                     class="imagen-procesada" 
                     alt="Imagen procesada"
                     title="Imagen con códigos detectados">
            </div>
        `;
    }
    
    html += '<div class="codigos-detectados">';
    datos.resultados.forEach((resultado, index) => {
        html += `
            <div class="codigo-detectado">
                <div class="codigo-header">
                    <h4>Código ${index + 1}</h4>
                    <span class="tipo-codigo">${resultado.tipo}</span>
                </div>
                <div class="codigo-content">
                    <p><strong>Datos originales:</strong> 
                        <span class="codigo-valor" title="Click para copiar">${resultado.datos_originales}</span>
                    </p>
                    <p><strong>Datos procesados:</strong> 
                        <span class="codigo-valor" title="Click para copiar">${resultado.datos_procesados}</span>
                    </p>
                </div>
            </div>
        `;
    });
    html += '</div></div>';
    
    resultadosDiv.innerHTML = html;
    resultadosDiv.style.display = 'block';
    
    // Hacer scroll a los resultados
    resultadosDiv.scrollIntoView({ behavior: 'smooth' });

    // Agregar event listeners para copiar al portapapeles
    document.querySelectorAll('.codigo-valor').forEach(elemento => {
        elemento.addEventListener('click', async function() {
            try {
                await navigator.clipboard.writeText(this.textContent);
                mostrarMensajeModal('Código copiado al portapapeles', false);
            } catch (err) {
                console.error('Error al copiar:', err);
            }
        });
    });
}

function limpiarResultados() {
    const resultadosDiv = document.getElementById('resultados');
    if (resultadosDiv) {
        resultadosDiv.innerHTML = '<p class="info-text">No se detectaron códigos de barras</p>';
    }
}

function mostrarSugerencias() {
    const resultadosDiv = document.getElementById('resultados');
    if (resultadosDiv) {
        resultadosDiv.innerHTML += `
            <div class="sugerencias-container">
                <h4>Sugerencias para mejorar la lectura:</h4>
                <ul>
                    <li>Asegúrese de que el código esté bien iluminado</li>
                    <li>Evite reflejos sobre el código</li>
                    <li>Centre el código en la imagen</li>
                    <li>Mantenga la cámara estable</li>
                    <li>Intente acercarse más al código (15-20cm)</li>
                    <li>Pruebe diferentes ángulos</li>
                </ul>
            </div>
        `;
    }
}