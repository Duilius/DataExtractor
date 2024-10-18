// camera.js
console.log('Cargando camera.js');

import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';
import { toggleCamera, capturePhoto, toggleVoiceCapture, switchCamera } from './camera_functions.js';

let cameraOn = false;
let recognition;
let isVoiceCaptureActive = false;


/*
if (tomarFotoBtn) {
    tomarFotoBtn.removeEventListener('click', capturePhoto); // Elimina listeners previos
    tomarFotoBtn.addEventListener('click', capturePhoto);
}
*/


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


function startVoiceCapture() {
    
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'es-ES';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const command = event.results[event.results.length - 1][0].transcript.toLowerCase();
        if (command.includes('tomar foto') || command.includes('capturar')) {
            capturePhoto();
        }
    };

    recognition.onend = () => {
        if (isVoiceCaptureActive) {
            recognition.start();
        }
    };

    recognition.start();
    isVoiceCaptureActive = true;
    document.getElementById('voiceCaptureBtn').textContent = 'Detener Captura por Voz';
    speak('Captura por voz activada. Diga "tomar foto" o "capturar" en cualquier momento para tomar una foto.');
}

function stopVoiceCapture() {
    if (recognition) {
        recognition.stop();
        recognition.onend = null;
        recognition = null;
    }
    isVoiceCaptureActive = false;
    document.getElementById('voiceCaptureBtn').textContent = 'Foto por Voz';
    speak('Captura por voz desactivada');
}

function speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    speechSynthesis.speak(utterance);
}