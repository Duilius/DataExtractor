// camera.js
console.log('Cargando camera.js');

import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';

let cameraOn = false;
let recognition;
let isVoiceCaptureActive = false;

export function initializeCamera() {
    console.log('Inicializando cámara');
    const cameraToggle = document.getElementById('cameraToggle');
    const tomarFotoBtn = document.getElementById('tomarFoto');
    const voiceCaptureBtn = document.getElementById('voiceCaptureBtn');

    cameraToggle.addEventListener('click', toggleCamera);
    tomarFotoBtn.addEventListener('click', capturePhoto);
    voiceCaptureBtn.addEventListener('click', toggleVoiceCapture);
}

function toggleCamera() {
    if (!cameraOn) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                document.getElementById('cameraFeed').srcObject = stream;
                cameraOn = true;
                speak("Cámara encendida");
            })
            .catch(err => {
                console.error("Error al encender la cámara: ", err);
                speak("Error al encender la cámara");
            });
    } else {
        let stream = document.getElementById('cameraFeed').srcObject;
        let tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        document.getElementById('cameraFeed').srcObject = null;
        cameraOn = false;
        speak("Cámara apagada");
    }
}

async function capturePhoto() {
    if (!cameraOn) {
        speak("Por favor, enciende la cámara primero.");
        return;
    }

    const canvas = document.createElement('canvas');
    const video = document.getElementById('cameraFeed');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    try {
        const { imageData: processedImageData, resized } = await processImage(canvas.toDataURL('image/png'));
        const event = new CustomEvent('addToGallery', { detail: { imageData: processedImageData } });
        document.dispatchEvent(event);
        speak("Foto capturada");
        /*
        if (resized) {
            alert("La imagen capturada ha sido redimensionada para cumplir con el tamaño máximo permitido de 1024x1024 píxeles.");
        }
        */
        // Verificación adicional de las dimensiones
        const img = new Image();
        img.onload = function() {
            if (this.width > 1024 || this.height > 1024) {
                console.warn('Advertencia: La imagen capturada excede 1024x1024 píxeles.');
            }
        };
        img.src = processedImageData;

    } catch (error) {
        console.error("Error al procesar la imagen:", error);
        speak("Error al procesar la imagen");
        alert("Error al procesar la imagen capturada");
    }
}

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