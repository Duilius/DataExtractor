// gallery.js
console.log('Cargando gallery.js');

import { showLargeImage, closeLargeImage } from './imageEditor.js';
import { processImage } from './imageProcessor.js';
import { speak, mostrarMensajeModal } from './utils.js';
import { checkAuthBeforeProcessing } from './utils.js';

let isGalleryInitialized = false;

export function initializeGallery() {
    if (isGalleryInitialized) {
        console.warn('La galería ya fue inicializada');
        return;
    }

    console.log('Inicializando galería');
    setupGalleryButtons();
    setupDropZone();
    setupEventListeners();
    
    isGalleryInitialized = true;
}

function setupGalleryButtons() {
    const buttons = {
        'eliminarFoto': eliminarFotosSeleccionadas,
        'guardarFoto': mostrarOpcionesGuardado,
        'procesarFoto': () => {
            if (checkAuthBeforeProcessing()) {
                if (typeof window.procesarImagenes === 'function') {
                    window.procesarImagenes();
                } else {
                    console.error('La función procesarImagenes no está definida globalmente');
                    speak('Error: función de procesamiento no disponible');
                }
            }
        },
        'subirFoto': () => {
            const fileInput = document.getElementById('fileInput');
            if (fileInput) {
                fileInput.value = '';
                fileInput.click();
            }
        }
    };

    Object.entries(buttons).forEach(([id, handler]) => {
        const button = document.getElementById(id);
        if (button) {
            button.removeEventListener('click', handler);
            button.addEventListener('click', handler);
        } else {
            console.warn(`Botón "${id}" no encontrado`);
        }
    });

    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.removeEventListener('change', handleFileSelect);
        fileInput.addEventListener('change', handleFileSelect);
    } else {
        console.warn('Input de archivo no encontrado');
    }
}

function setupDropZone() {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) {
        console.warn('Zona de drop no encontrada');
        return;
    }

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    dropZone.addEventListener('dragover', () => dropZone.classList.add('drag-over'));
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    
    dropZone.addEventListener('drop', async (e) => {
        console.log('Archivos soltados en dropZone');
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            await handleFiles(e.dataTransfer.files);
        }
    });
}

function setupEventListeners() {
    document.addEventListener('photoTaken', event => addPhotoToGallery(event.detail));
    document.addEventListener('imageSaved', event => handleSavedImage(event.detail));
    document.addEventListener('addToGallery', event => 
        addPhotoToGallery(event.detail.imageData, event.detail.isEdited));
    document.addEventListener('change', event => {
        if (event.target.classList.contains('fotoCheckbox')) {
            activarBotones();
        }
    });
}

export async function addPhotoToGallery(imgSrc, isEdited = false) {
    console.log("Añadiendo foto a la galería");
    try {
        if (!imgSrc) {
            throw new Error('No se proporcionó imagen para añadir a la galería');
        }

        const { imageData: processedImageData, resized } = await processImage(imgSrc);
        const miniaturas = document.getElementById('miniaturas');
        
        if (!miniaturas) {
            throw new Error('Contenedor de miniaturas no encontrado');
        }

        const miniaturaContainer = createMiniatureContainer(processedImageData, isEdited);
        miniaturas.appendChild(miniaturaContainer);
        activarBotones();

        if (resized) {
            mostrarMensajeModal("La imagen ha sido redimensionada para optimizar el rendimiento", false);
        }

        speak("Imagen añadida a la galería");
        return processedImageData;

    } catch (error) {
        console.error("Error al procesar la imagen para la galería:", error);
        mostrarMensajeModal("Error al añadir la imagen a la galería: " + error.message, true);
        throw error;
    }
}

function createMiniatureContainer(imgSrc, isEdited = false) {
    const container = document.createElement('div');
    container.className = `miniatura-container${isEdited ? ' editada' : ''}`;
    
    const img = document.createElement('img');
    img.src = imgSrc;
    img.className = 'miniatura';
    img.addEventListener('click', () => showLargeImage(imgSrc));
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'fotoCheckbox';

    const deleteButton = document.createElement('button');
    deleteButton.className = 'delete-button';
    deleteButton.innerHTML = '×';
    deleteButton.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('¿Está seguro de eliminar esta imagen?')) {
            container.remove();
            activarBotones();
            mostrarMensajeModal('Imagen eliminada', false);
        }
    });

    container.appendChild(img);
    container.appendChild(checkbox);
    container.appendChild(deleteButton);

    return container;
}

async function handleFileSelect(e) {
    console.log('Evento de selección de archivo disparado');
    console.log('Archivos seleccionados:', e.target.files);
    if (!checkAuthBeforeProcessing()) {
        return;
    }
    await handleFiles(e.target.files);
}

async function handleFiles(files) {
    console.log('Iniciando procesamiento de archivos');
    console.log('Archivos a procesar:', files);
    const imageFiles = Array.from(files).filter(file => 
        file.type.startsWith('image/') || 
        file.type === 'image/webp'
    );
    
    if (imageFiles.length === 0) {
        mostrarMensajeModal('Por favor, seleccione archivos de imagen válidos', true);
        return;
    }

    for (const file of imageFiles) {
        try {
            const reader = new FileReader();
            const imageData = await new Promise((resolve, reject) => {
                reader.onload = e => resolve(e.target.result);
                reader.onerror = () => reject(new Error(`Error al leer el archivo: ${file.name}`));
                reader.readAsDataURL(file);
            });

            await addPhotoToGallery(imageData);
        } catch (error) {
            console.error(`Error al procesar el archivo ${file.name}:`, error);
            mostrarMensajeModal(`Error al procesar ${file.name}: ${error.message}`, true);
        }
    }
}

function eliminarFotosSeleccionadas() {
    const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
    if (fotosSeleccionadas.length === 0) {
        mostrarMensajeModal("Por favor, seleccione al menos una foto para eliminar", true);
        return;
    }
    
    if (confirm(`¿Está seguro de que desea eliminar ${fotosSeleccionadas.length} foto(s)?`)) {
        fotosSeleccionadas.forEach(checkbox => checkbox.closest('.miniatura-container').remove());
        activarBotones();
        mostrarMensajeModal(`${fotosSeleccionadas.length} foto(s) eliminada(s)`, false);
    }
}

function mostrarOpcionesGuardado() {
    if (!checkAuthBeforeProcessing()) {
        return;
    }

    const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
    if (fotosSeleccionadas.length === 0) {
        mostrarMensajeModal("Por favor, seleccione al menos una foto para guardar", true);
        return;
    }

    const dialog = document.createElement('div');
    dialog.className = 'save-options-dialog';
    dialog.innerHTML = `
        <div class="save-options-content">
            <h3>Opciones de Guardado</h3>
            <button onclick="guardarEnDrive()">Guardar en Drive</button>
            <button onclick="guardarEnServidor()">Guardar en Servidor</button>
            <button onclick="guardarEnLocal()">Descargar a PC</button>
            <button onclick="this.parentElement.parentElement.remove()">Cancelar</button>
        </div>
    `;
    document.body.appendChild(dialog);
}

async function handleSavedImage({ originalSrc, editedImageData }) {
    try {
        const { imageData: processedImageData } = await processImage(editedImageData);
        const originalMiniature = Array.from(document.querySelectorAll('.miniatura'))
            .find(img => img.src === originalSrc);

        if (originalMiniature) {
            const newContainer = createMiniatureContainer(processedImageData, true);
            originalMiniature.closest('.miniatura-container').insertAdjacentElement('afterend', newContainer);
        } else {
            await addPhotoToGallery(processedImageData, true);
        }

        closeLargeImage();
        activarBotones();
        mostrarMensajeModal('Imagen guardada exitosamente', false);
    } catch (error) {
        console.error("Error al procesar la imagen editada:", error);
        mostrarMensajeModal("Error al guardar la imagen editada: " + error.message, true);
    }
}

export function activarBotones() {
    const hayFotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked').length > 0;
    const botones = ['eliminarFoto', 'guardarFoto', 'procesarFoto'];
    
    botones.forEach(id => {
        const boton = document.getElementById(id);
        if (boton) {
            boton.disabled = !hayFotosSeleccionadas;
            boton.classList.toggle('disabled', !hayFotosSeleccionadas);
        }
    });
}

window.guardarEnDrive = function() {
    mostrarMensajeModal('Función de guardado en Drive en desarrollo', true);
}

window.guardarEnServidor = function() {
    mostrarMensajeModal('Función de guardado en servidor en desarrollo', true);
}

window.guardarEnLocal = async function() {
    const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
    if (fotosSeleccionadas.length === 0) return;

    try {
        for (const checkbox of fotosSeleccionadas) {
            const img = checkbox.closest('.miniatura-container').querySelector('.miniatura');
            const response = await fetch(img.src);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `imagen_${Date.now()}.webp`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
        mostrarMensajeModal('Imágenes descargadas exitosamente', false);
    } catch (error) {
        console.error('Error al descargar imágenes:', error);
        mostrarMensajeModal('Error al descargar imágenes', true);
    }
}

export {
    handleSavedImage
};