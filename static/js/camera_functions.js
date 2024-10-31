// camera_functions.js

// Importaciones
import { speak } from './utils.js';
import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';
import { addPhotoToGallery, activarBotones } from './gallery.js';

// Variables globales
let isCapturing = false;
let captureCount = 0;
let cameraOn = false;
let recognition = null;
let isVoiceCaptiveActive = false;
let isProcessing = false;
let currentCameraIndex = 0;
let cameras = [];

// Funciones principales
async function getCameras() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter(device => device.kind === 'videoinput');
}

async function toggleCamera() {
    if (cameras.length === 0) {
        cameras = await getCameras();
    }

    if (!cameraOn) {
        try {
            const rearCamera = cameras.find(camera => /(back|rear|environment|behind)/i.test(camera.label));
            const constraints = {
                video: rearCamera 
                    ? { deviceId: { exact: rearCamera.deviceId } }
                    : { facingMode: 'environment' }
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            document.getElementById('cameraFeed').srcObject = stream;
            cameraOn = true;
            speak("Cámara trasera encendida");
        } catch (err) {
            console.error("Error al encender la cámara trasera: ", err);
            speak("Error al encender la cámara");
        }
    } else {
        let stream = document.getElementById('cameraFeed').srcObject;
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            document.getElementById('cameraFeed').srcObject = null;
            cameraOn = false;
            speak("Cámara apagada");
        }
    }
}

async function capturePhoto() {
    captureCount++;
    console.log(`Intento de captura #${captureCount}`);
    
    if (isCapturing) {
        speak("Ya se está capturando una foto, por favor espere");
        return;
    }
    
    if (!cameraOn) {
        speak("Por favor, encienda la cámara primero");
        return;
    }

    isCapturing = true;

    try {
        const canvas = document.createElement('canvas');
        const video = document.getElementById('cameraFeed');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);

        const { imageData: processedImageData } = await processImage(canvas.toDataURL('image/png'));
        await addPhotoToGallery(processedImageData);
        // Procesar inmediatamente después de capturar
        await procesarCodigoBarras(processedImageData);
        speak("Foto capturada y procesada");

    } catch (error) {
        console.error("Error al procesar la imagen:", error);
        speak("Error al procesar la imagen");
    } finally {
        isCapturing = false;
    }
}

async function switchCamera() {
    if (!cameraOn) {
        speak("Por favor, enciende la cámara primero.");
        return;
    }

    currentCameraIndex = (currentCameraIndex + 1) % cameras.length;
    await toggleCamera();
    await toggleCamera();
    speak("Cambiando a la siguiente cámara");
}

// Funciones de captura por voz
function toggleVoiceCapture() {
    if (!cameraOn) {
        speak("Por favor, enciende la cámara primero");
        return;
    }

    if (isVoiceCaptiveActive) {
        stopVoiceCapture();
    } else {
        startVoiceCapture();
    }
}

function startVoiceCapture() {
    if (recognition) {
        recognition.stop();
    }
    
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'es-ES';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const command = event.results[event.results.length - 1][0].transcript.toLowerCase();
        console.log('Comando detectado:', command);
        if (command.includes('tomar foto') || command.includes('capturar')) {
            capturePhoto();
        }
    };

    recognition.onend = () => {
        if (isVoiceCaptiveActive) {
            recognition.start();
        }
    };

    recognition.start();
    isVoiceCaptiveActive = true;
    document.getElementById('voiceCaptureBtn').textContent = 'Detener Captura por Voz';
    speak('Captura por voz activada. Diga "tomar foto" o "capturar" en cualquier momento para tomar una foto.');
}

function stopVoiceCapture() {
    if (recognition) {
        recognition.stop();
        recognition.onend = null;
        recognition = null;
    }
    isVoiceCaptiveActive = false;
    document.getElementById('voiceCaptureBtn').textContent = 'Foto por Voz';
    speak('Captura por voz desactivada');
}

// Funciones de utilidad
function generateUUID() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], {type: mimeString});
}

// Exportaciones
export { 
    toggleCamera, 
    capturePhoto, 
    toggleVoiceCapture, 
    switchCamera 
};

// Event listeners globales
if (typeof window !== 'undefined') {
    window.toggleCamera = toggleCamera;
    window.capturePhoto = capturePhoto;
    window.toggleVoiceCapture = toggleVoiceCapture;
}