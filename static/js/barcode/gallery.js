// gallery.js
import { speak } from './utils.js';
import { openImageEditor } from './editor.js';
import { procesarCodigoBarras } from './processor.js';

let selectedImages = new Set();

export function initializeGallery() {
    const procesarBtn = document.getElementById('procesarSeleccionadas');
    const eliminarBtn = document.getElementById('eliminarSeleccionadas');
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    
    if (procesarBtn) {
        procesarBtn.addEventListener('click', procesarSeleccionadas);
    }
    
    if (eliminarBtn) {
        eliminarBtn.addEventListener('click', eliminarSeleccionadas);
    }

    if (dropZone) {
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('dragleave', handleDragLeave);
        dropZone.addEventListener('drop', handleDrop);
        dropZone.addEventListener('click', () => fileInput?.click());
    }

    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => fileInput?.click());
    }

    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('miniatura-checkbox')) {
            actualizarSeleccion(e.target);
        }
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('drag-over');
}

async function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('drag-over');

    const files = [...e.dataTransfer.files].filter(file => file.type.startsWith('image/'));
    if (files.length === 0) {
        speak("Por favor, solo arrastre archivos de imagen");
        return;
    }

    await processFiles(files);
}

async function handleFileSelect(e) {
    e.preventDefault(); // Prevenir comportamiento por defecto
    const files = [...e.target.files].filter(file => file.type.startsWith('image/'));
    if (files.length === 0) {
        speak("Por favor, seleccione archivos de imagen");
        return;
    }

    await processFiles(files);
    e.target.value = ''; // Limpiar el input después de procesar
}

async function processFiles(files) {
    showLoading();
    try {
        for (const file of files) {
            const reader = new FileReader();
            await new Promise((resolve, reject) => {
                reader.onload = async () => {
                    try {
                        await addToGallery(reader.result);
                        resolve();
                    } catch (error) {
                        reject(error);
                    }
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        }
        speak(`${files.length} imágenes añadidas a la galería`);
    } catch (error) {
        console.error('Error procesando archivos:', error);
        speak("Error al procesar algunas imágenes");
    } finally {
        hideLoading();
    }
}

export async function addToGallery(imageData, isEdited = false) {
    const miniaturas = document.getElementById('miniaturas');
    if (!miniaturas) return;

    const container = document.createElement('div');
    container.className = `miniatura-container ${isEdited ? 'edited' : ''}`;

    const imgWrapper = document.createElement('div');
    imgWrapper.className = 'miniatura-wrapper';

    const img = document.createElement('img');
    img.src = imageData;
    img.className = 'miniatura';
    img.addEventListener('click', () => openImageEditor(imageData));

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'miniatura-checkbox';
    checkbox.dataset.imageData = imageData;

    imgWrapper.appendChild(img);
    container.appendChild(imgWrapper);
    container.appendChild(checkbox);
    miniaturas.appendChild(container);

    actualizarBotonesGaleria();

    // Procesar automáticamente si es una nueva captura
    if (!isEdited) {
        await procesarCodigoBarras(imageData);
    }
}

function actualizarSeleccion(checkbox) {
    if (checkbox.checked) {
        selectedImages.add(checkbox.dataset.imageData);
    } else {
        selectedImages.delete(checkbox.dataset.imageData);
    }
    actualizarBotonesGaleria();
}

function actualizarBotonesGaleria() {
    const procesarBtn = document.getElementById('procesarSeleccionadas');
    const eliminarBtn = document.getElementById('eliminarSeleccionadas');
    
    const haySeleccionadas = selectedImages.size > 0;
    
    if (procesarBtn) procesarBtn.disabled = !haySeleccionadas;
    if (eliminarBtn) eliminarBtn.disabled = !haySeleccionadas;
}

async function procesarSeleccionadas() {
    if (selectedImages.size === 0) {
        speak("Por favor, seleccione al menos una imagen");
        return;
    }

    speak(`Procesando ${selectedImages.size} imágenes`);
    showLoading();
    
    try {
        for (const imageData of selectedImages) {
            await procesarCodigoBarras(imageData);
        }
    } catch (error) {
        console.error('Error al procesar imágenes:', error);
        speak("Error al procesar las imágenes seleccionadas");
    } finally {
        hideLoading();
    }
}

function eliminarSeleccionadas() {
    if (selectedImages.size === 0) {
        speak("No hay imágenes seleccionadas para eliminar");
        return;
    }

    const mensaje = `¿Desea eliminar ${selectedImages.size} imágenes?`;
    if (confirm(mensaje)) {
        const miniaturas = document.getElementById('miniaturas');
        const checkboxes = miniaturas.querySelectorAll('.miniatura-checkbox:checked');
        
        checkboxes.forEach(checkbox => {
            checkbox.closest('.miniatura-container').remove();
        });

        selectedImages.clear();
        actualizarBotonesGaleria();
        speak("Imágenes eliminadas");
    }
}

function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="loading-spinner"></div>';
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

//export { initializeGallery };