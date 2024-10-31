// gallery.js
console.log('Cargando gallery.js');

import { showLargeImage, closeLargeImage } from './imageEditor.js';
import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';
import { speak } from './utils.js';

export function initializeGallery() {
    console.log('Inicializando galería');
    const eliminarFotoBtn = document.getElementById('eliminarFoto');
    const guardarFotoBtn = document.getElementById('guardarFoto');
    const procesarFotoBtn = document.getElementById('procesarFoto');
    const subirFotoBtn = document.getElementById('subirFoto');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');

    if (eliminarFotoBtn) {
        eliminarFotoBtn.addEventListener('click', eliminarFotosSeleccionadas);
    } else {
        console.error('Botón "eliminarFoto" no encontrado');
    }

    if (guardarFotoBtn) {
        guardarFotoBtn.addEventListener('click', mostrarOpcionesGuardado);
    } else {
        console.error('Botón "guardarFoto" no encontrado');
    }

    if (procesarFotoBtn) {
        procesarFotoBtn.addEventListener('click', () => {
            if (typeof window.procesarImagenes === 'function') {
                window.procesarImagenes();
            } else {
                console.error('La función procesarImagenes no está definida globalmente');
                speak('Error: función de procesamiento no disponible');
            }
        });
    } else {
        console.error('Botón "procesarFoto" no encontrado');
    }

    if (subirFotoBtn && fileInput) {
        subirFotoBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFileSelect);
    } else {
        console.error('Botón "subirFoto" o inputFile no encontrado');
    }

    if (dropZone) {
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('dragleave', handleDragLeave);
        dropZone.addEventListener('drop', handleDrop);
    } else {
        console.error('Zona de arrastrar y soltar no encontrada');
    }

    document.addEventListener('photoTaken', event => addPhotoToGallery(event.detail));
    document.addEventListener('imageSaved', event => handleSavedImage(event.detail));
    document.addEventListener('addToGallery', event => addPhotoToGallery(event.detail.imageData, event.detail.isEdited));
    
    activarBotones();
}

export async function addPhotoToGallery(imgSrc, isEdited = false) {
    console.log("Función addPhotoToGallery iniciada");
    try {
        const { imageData: processedImageData, resized } = await processImage(imgSrc);
        const miniaturas = document.getElementById('miniaturas');
        const miniaturaContainer = createMiniatureContainer(processedImageData, isEdited);
        miniaturas.appendChild(miniaturaContainer);
        activarBotones();

        console.log("Foto añadida a la galería");
        speak("Imagen añadida a la galería");

        const img = new Image();
        img.onload = function() {
            if (this.width > 1024 || this.height > 1024) {
                console.warn('Advertencia: La imagen en la galería excede 1024x1024 píxeles.');
            }
        };
        img.src = processedImageData;

    } catch (error) {
        console.error("Error al procesar la imagen para la galería:", error);
        speak("Error al añadir la imagen a la galería");
    }
}

function createMiniatureContainer(imgSrc, isEdited = false) {
    const miniaturaContainer = document.createElement('div');
    miniaturaContainer.className = `miniatura-container${isEdited ? ' editada' : ''}`;
    
    const img = document.createElement('img');
    img.src = imgSrc;
    img.className = 'miniatura';
    img.addEventListener('click', () => showLargeImage(img.src));
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'fotoCheckbox';

    miniaturaContainer.appendChild(img);
    miniaturaContainer.appendChild(checkbox);

    return miniaturaContainer;
}

function eliminarFotosSeleccionadas() {
    const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
    if (fotosSeleccionadas.length === 0) {
        speak("Por favor, seleccione al menos una foto para eliminar");
        return;
    }
    
    if (confirm(`¿Está seguro de que desea eliminar ${fotosSeleccionadas.length} foto(s)?`)) {
        fotosSeleccionadas.forEach(checkbox => checkbox.parentElement.remove());
        activarBotones();
        speak(`${fotosSeleccionadas.length} fotos eliminadas`);
    }
}

function mostrarOpcionesGuardado() {
    const options = ["Guardar en Drive", "Guardar en Servidor", "Guardar en Local"];
    const selectedOption = prompt(`Seleccione una opción de guardado:\n1. ${options[0]}\n2. ${options[1]}\n3. ${options[2]}\n\nIngrese el número de la opción:`);

    switch(selectedOption) {
        case "1": guardarEnDrive(); break;
        case "2": guardarEnServidor(); break;
        case "3": guardarEnLocal(); break;
        default: speak("Opción no válida o cancelada");
    }
}

function guardarEnDrive() {
    speak("Función guardar en Drive no implementada");
}

function guardarEnServidor() {
    speak("Función guardar en servidor no implementada");
}

function guardarEnLocal() {
    speak("Función guardar en local no implementada");
}

async function handleFileSelect(e) {
    await handleFiles(e.target.files);
}

function handleDragOver(e) {
    e.preventDefault();
    e.target.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.target.classList.remove('drag-over');
}

async function handleDrop(e) {
    e.preventDefault();
    e.target.classList.remove('drag-over');
    await handleFiles(e.dataTransfer.files);
}

async function handleFiles(files) {
    for (let file of files) {
        if (file.type.startsWith('image/')) {
            try {
                const reader = new FileReader();
                const imageData = await new Promise((resolve, reject) => {
                    reader.onload = (e) => resolve(e.target.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                });

                await addPhotoToGallery(imageData);
            } catch (error) {
                console.error("Error al procesar el archivo:", error);
                speak(`Error al procesar el archivo ${file.name}`);
            }
        }
    }
}

export function activarBotones() {
    const checkboxes = document.querySelectorAll('.fotoCheckbox:checked');
    const activar = checkboxes.length > 0;
    ['eliminarFoto', 'guardarFoto', 'procesarFoto'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.disabled = !activar;
        } else {
            console.warn(`Botón "${id}" no encontrado`);
        }
    });
}

async function handleSavedImage({ originalSrc, editedImageData }) {
    try {
        const processedImageData = await processImage(editedImageData);
        const originalMiniature = document.querySelector(`img.miniatura[src="${originalSrc}"]`);
        if (originalMiniature) {
            const newMiniatureContainer = createMiniatureContainer(processedImageData, true);
            originalMiniature.parentNode.parentNode.insertBefore(newMiniatureContainer, originalMiniature.parentNode.nextSibling);
        } else {
            addPhotoToGallery(processedImageData);
        }
        closeLargeImage();
        activarBotones();
    } catch (error) {
        console.error("Error al procesar la imagen editada:", error);
        speak("Error al guardar la imagen editada");
    }
}

document.addEventListener('change', function(event) {
    if (event.target.classList.contains('fotoCheckbox')) {
        activarBotones();
    }
});