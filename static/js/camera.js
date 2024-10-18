// camera.js
console.log('Cargando camera.js');

import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';
import { toggleCamera, capturePhoto, toggleVoiceCapture, switchCamera } from './camera_functions.js';

let cameraOn = false;
let recognition;
let isVoiceCaptureActive = false;

export function initializeCamera() {
    console.log('Inicializando cámara');
    const cameraToggle = document.getElementById('cameraToggle');
    const tomarFotoBtn = document.getElementById('tomarFoto');
    const voiceCaptureBtn = document.getElementById('voiceCaptureBtn');
    const switchCameraBtn = document.getElementById('switchCameraBtn');

    if (cameraToggle) cameraToggle.addEventListener('click', toggleCamera);
    if (tomarFotoBtn) tomarFotoBtn.addEventListener('click', capturePhoto);
    if (voiceCaptureBtn) voiceCaptureBtn.addEventListener('click', toggleVoiceCapture);
    if (switchCameraBtn) switchCameraBtn.addEventListener('click', switchCamera);
}


/*
function toggleVoiceCapture() {
    if (!cameraOn) {
        speak("Por favor, enciende la cámara primero.");
        return;
    }

    if (isVoiceCaptureActive) {
        stopVoiceCapture();
    } else {
        startVoiceCapture();
    }
}
*/

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