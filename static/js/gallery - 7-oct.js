// gallery.js
console.log('Cargando gallery.js');

import { procesarImagenes } from './camera_functions.js';
import { showLargeImage, closeLargeImage } from './imageEditor.js';

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
            if (typeof procesarImagenes === 'function') {
                procesarImagenes();
            } else {
                console.error('La función procesarImagenes no está definida');
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
    
    // Activar botones inicialmente
    activarBotones();
}


function addPhotoToGallery(imgSrc) {
    const miniaturas = document.getElementById('miniaturas');
    const miniaturaContainer = createMiniatureContainer(imgSrc);
    miniaturas.appendChild(miniaturaContainer);
    activarBotones();
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
        alert("Por favor, seleccione al menos una foto para eliminar.");
        return;
    }
    
    if (confirm(`¿Está seguro de que desea eliminar ${fotosSeleccionadas.length} foto(s)?`)) {
        fotosSeleccionadas.forEach(checkbox => checkbox.parentElement.remove());
        activarBotones();
    }
}

function mostrarOpcionesGuardado() {
    const options = ["Guardar en Drive", "Guardar en Servidor", "Guardar en Local"];
    const selectedOption = prompt(`Seleccione una opción de guardado:\n1. ${options[0]}\n2. ${options[1]}\n3. ${options[2]}\n\nIngrese el número de la opción:`);

    switch(selectedOption) {
        case "1": guardarEnDrive(); break;
        case "2": guardarEnServidor(); break;
        case "3": guardarEnLocal(); break;
        default: alert("Opción no válida o cancelada.");
    }
}

function guardarEnDrive() {
    alert("Función guardarEnDrive no implementada");
}

function guardarEnServidor() {
    alert("Función guardarEnServidor no implementada");
}

function guardarEnLocal() {
    alert("Función guardarEnLocal no implementada");
}

function handleFileSelect(e) {
    handleFiles(e.target.files);
}

function handleDragOver(e) {
    e.preventDefault();
    e.target.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.target.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.target.classList.remove('drag-over');
    handleFiles(e.dataTransfer.files);
}

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => addPhotoToGallery(e.target.result);
            reader.readAsDataURL(file);
        }
    });
}

// Modificar la función activarBotones para que sea más robusta
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


function handleSavedImage({ originalSrc, editedImageData }) {
    const originalMiniature = document.querySelector(`img.miniatura[src="${originalSrc}"]`);
    if (originalMiniature) {
        const newMiniatureContainer = createMiniatureContainer(editedImageData, true);
        originalMiniature.parentNode.parentNode.insertBefore(newMiniatureContainer, originalMiniature.parentNode.nextSibling);
    } else {
        addPhotoToGallery(editedImageData);
    }
    closeLargeImage();
    activarBotones();
}

// Event listener para activar botones cuando se marcan/desmarcan checkboxes
document.addEventListener('change', function(event) {
    if (event.target.classList.contains('fotoCheckbox')) {
        activarBotones();
    }
});

// Asegurarse de que este event listener se añada solo una vez
document.removeEventListener('change', checkboxChangeHandler);
document.addEventListener('change', checkboxChangeHandler);

function checkboxChangeHandler(event) {
    if (event.target.classList.contains('fotoCheckbox')) {
        activarBotones();
    }
}