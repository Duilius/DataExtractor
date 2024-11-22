// camera.js
console.log('Cargando camera.js');

import { speak } from './utils.js';
import { toggleCamera, capturePhoto, toggleVoiceCapture, switchCamera } from './camera_functions.js';

export function initializeCamera() {
    console.log('Inicializando cámara');
    const cameraToggle = document.getElementById('cameraToggle');
    const tomarFotoBtn = document.getElementById('tomarFoto');
    const voiceCaptureBtn = document.getElementById('voiceCaptureBtn');
    const switchCameraBtn = document.getElementById('switchCameraBtn');

    if (cameraToggle) {
        cameraToggle.removeEventListener('click', toggleCamera);
        cameraToggle.addEventListener('click', toggleCamera);
        console.log('Evento click agregado a cameraToggle');
    }
    
    if (tomarFotoBtn) {
        tomarFotoBtn.removeEventListener('click', capturePhoto);
        tomarFotoBtn.addEventListener('click', function(event) {
            console.log('Botón tomarFoto clickeado');
            event.preventDefault();
            capturePhoto();
        });
        console.log('Evento click agregado a tomarFotoBtn');
    }
    
    if (voiceCaptureBtn) {
        voiceCaptureBtn.removeEventListener('click', toggleVoiceCapture);
        voiceCaptureBtn.addEventListener('click', toggleVoiceCapture);
        console.log('Evento click agregado a voiceCaptureBtn');
    }
    
    if (switchCameraBtn) {
        switchCameraBtn.removeEventListener('click', switchCamera);
        switchCameraBtn.addEventListener('click', switchCamera);
        console.log('Evento click agregado a switchCameraBtn');
    }
}