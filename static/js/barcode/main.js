// main.js
import { initializeCamera } from './camera.js';
import { initializeUtils, initializeVoice, speak } from './utils.js';
import { initializeGallery, addToGallery } from './gallery.js';  // Añadir addToGallery aquí
import { initializeImageEditor } from './editor.js';

window.addEventListener('DOMContentLoaded', (event) => {
    console.log('Inicializando lector de códigos de barras');
    
    // Inicializar todos los módulos
    initializeCamera();
    initializeUtils();
    initializeVoice();
    initializeGallery();
    initializeImageEditor();

    // Manejo de errores global
    window.addEventListener('error', function(e) {
        console.error('Error global:', e.error);
        speak('Se ha producido un error en la aplicación', 1, 1);
    });

    // Evento personalizado para actualizar la galería
    document.addEventListener('photoTaken', function(e) {
        if (e.detail && e.detail.imageData) {
            addToGallery(e.detail.imageData);
        }
    });

    // Verificar permisos de cámara al inicio
    checkCameraPermissions();
});

async function checkCameraPermissions() {
    try {
        await navigator.mediaDevices.getUserMedia({ video: true });
        console.log('Permisos de cámara concedidos');
    } catch (err) {
        console.error('Error al solicitar permisos de cámara:', err);
        speak('Por favor, permite el acceso a la cámara para usar la aplicación');
    }
}

// Función global para cerrar el modal
window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
};