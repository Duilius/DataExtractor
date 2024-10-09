// main.js

console.log('Cargando main.js');

import { procesarImagenes, toggleCamera, capturePhoto, toggleVoiceCapture } from './camera_functions.js';

import { initializeCamera } from './camera.js';
import { initializeGallery, activarBotones } from './gallery.js';
import { initializeImageEditor } from './imageEditor.js';
import { initializeFormHandler, mostrarFormulario } from './formHandler.js';
import { initializeUtils } from './utils.js';
import { initializeSearch } from './search.js';
import { initializeWorkerInfo } from './worker_info.js';
//import { procesarImagenes } from './camera_functions.js';
import './imageProcessor.js';

window.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM completamente cargado en main.js');
    
    initializeCamera();
    initializeGallery();
    initializeImageEditor();
    initializeFormHandler();
    initializeUtils();
    initializeSearch();
    initializeWorkerInfo();

    // Hacer procesarImagenes disponible globalmente
    window.procesarImagenes = procesarImagenes;
});

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modal');
    const closeBtn = document.querySelector('.close');

    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = "none";
        }
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    window.closeModal = function() {
        modal.style.display = "none";
    }
});