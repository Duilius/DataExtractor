// camera.js
import { speak } from './utils.js';
import { procesarCodigoBarras } from './processor.js';
import { addToGallery } from './gallery.js';

let cameraOn = false;
let isCapturing = false;
let isVoiceCaptureActive = false;
let recognition = null;

export function initializeCamera() {
    console.log('Inicializando cámara para códigos de barras');
    const cameraToggle = document.getElementById('cameraToggle');
    const tomarFotoBtn = document.getElementById('tomarFoto');
    const voiceCaptureBtn = document.getElementById('voiceCaptureBtn');

    if (cameraToggle) {
        cameraToggle.removeEventListener('click', toggleCamera);
        cameraToggle.addEventListener('click', toggleCamera);
    }
    
    if (tomarFotoBtn) {
        tomarFotoBtn.removeEventListener('click', capturePhoto);
        tomarFotoBtn.addEventListener('click', async function(event) {
            console.log('Botón tomarFoto clickeado');
            event.preventDefault();
            await capturePhoto();
        });
    }

    if (voiceCaptureBtn) {
        voiceCaptureBtn.addEventListener('click', toggleVoiceCapture);
    }
}

async function toggleCamera() {
    try {
        if (!cameraOn) {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            });
            const video = document.getElementById('cameraFeed');
            if (video) {
                video.srcObject = stream;
                await video.play();
                cameraOn = true;
                speak("Cámara encendida");
            }
        } else {
            const video = document.getElementById('cameraFeed');
            if (video && video.srcObject) {
                const stream = video.srcObject;
                stream.getTracks().forEach(track => track.stop());
                video.srcObject = null;
                cameraOn = false;
                speak("Cámara apagada");
            }
        }
    } catch (err) {
        console.error("Error de cámara:", err);
        speak("Error al acceder a la cámara");
    }
}

async function capturePhoto() {
    if (isCapturing) {
        speak("Procesando imagen anterior, por favor espere");
        return;
    }
    
    if (!cameraOn) {
        speak("Por favor, encienda la cámara primero");
        return;
    }

    isCapturing = true;
    try {
        const video = document.getElementById('cameraFeed');
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        
        const imageData = canvas.toDataURL('image/jpeg');
        
        // Agregar a galería y procesar inmediatamente
        await addToGallery(imageData);
        await procesarCodigoBarras(imageData);
        
        speak("Foto capturada y procesada");
        
    } catch (error) {
        console.error("Error al capturar:", error);
        speak("Error al capturar la imagen");
    } finally {
        isCapturing = false;
    }
}

function toggleVoiceCapture() {
    if (!cameraOn) {
        speak("Por favor, encienda la cámara primero");
        return;
    }

    if (isVoiceCaptureActive) {
        stopVoiceCapture();
    } else {
        startVoiceCapture();
    }
}

function startVoiceCapture() {
    if (!('webkitSpeechRecognition' in window)) {
        speak("Lo siento, tu navegador no soporta reconocimiento de voz");
        return;
    }

    recognition = new webkitSpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
        isVoiceCaptureActive = true;
        document.getElementById('voiceCaptureBtn').textContent = 'Detener Voz';
        speak("Captura por voz activada. Di 'tomar foto' o 'capturar' para tomar una foto");
    };

    recognition.onresult = async (event) => {
        const comando = event.results[event.results.length - 1][0].transcript.toLowerCase();
        if (comando.includes('tomar foto') || comando.includes('capturar')) {
            await capturePhoto();
        }
    };

    recognition.onerror = (event) => {
        console.error('Error en reconocimiento de voz:', event.error);
        stopVoiceCapture();
    };

    recognition.onend = () => {
        if (isVoiceCaptureActive) {
            recognition.start();
        }
    };

    recognition.start();
}

function stopVoiceCapture() {
    if (recognition) {
        recognition.stop();
        recognition = null;
    }
    isVoiceCaptureActive = false;
    document.getElementById('voiceCaptureBtn').textContent = 'Foto por Voz';
    speak("Captura por voz desactivada");
}

export { toggleCamera, capturePhoto, toggleVoiceCapture };