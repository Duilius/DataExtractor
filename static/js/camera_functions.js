// camera_functions.js
import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';

export { procesarImagenes, toggleCamera, capturePhoto, toggleVoiceCapture };

let cameraOn = false;
let recognition;
let isVoiceCaptureActive = false;
let cropper;

let currentCameraIndex = 0;
let cameras = [];

async function toggleCamera() {
    if (cameras.length === 0) {
        cameras = await getCameras();
    }

    if (!cameraOn) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { deviceId: { exact: cameras[currentCameraIndex].deviceId } }
            });
            document.getElementById('cameraFeed').srcObject = stream;
            cameraOn = true;
            speak("Cámara encendida");
        } catch (err) {
            console.error("Error al encender la cámara: ", err);
            speak("Error al encender la cámara");
        }
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
        const processedImageData = await processImage(canvas.toDataURL('image/png'));
        addPhotoToGallery(processedImageData);
    } catch (error) {
        console.error("Error al procesar la imagen:", error);
        speak("Error al procesar la imagen");
    }
}

function addPhotoToGallery(imgSrc) {
    const img = document.createElement('img');
    img.src = imgSrc;
    img.className = 'miniatura';
    img.addEventListener('click', () => showLargeImage(img.src));
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'fotoCheckbox';

    const miniaturaContainer = document.createElement('div');
    miniaturaContainer.appendChild(img);
    miniaturaContainer.appendChild(checkbox);
    document.getElementById('miniaturas').appendChild(miniaturaContainer);

    window.fotosNoGuardadas = true;
    activarBotones();
    speak('Foto añadida a la galería');
}

async function showLargeImage(src) {
    const overlay = document.createElement('div');
    overlay.className = 'image-overlay';
    
    const imageContainer = document.createElement('div');
    imageContainer.className = 'image-container';
    
    const largeImg = document.createElement('img');
    largeImg.src = src;
    largeImg.className = 'large-image';
    
    const editorContainer = document.createElement('div');
    editorContainer.className = 'editor-container';
    
    const cropButton = document.createElement('button');
    cropButton.textContent = 'Recortar';
    cropButton.onclick = () => initCrop(largeImg);
    
    const rotateLeftButton = document.createElement('button');
    rotateLeftButton.textContent = 'Rotar Izquierda';
    rotateLeftButton.onclick = () => rotateImage(largeImg, -90);
    
    const rotateRightButton = document.createElement('button');
    rotateRightButton.textContent = 'Rotar Derecha';
    rotateRightButton.onclick = () => rotateImage(largeImg, 90);
    
    const saveButton = document.createElement('button');
    saveButton.textContent = 'Guardar Cambios';
    saveButton.onclick = () => saveEditedImage(largeImg, src);
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'X';
    closeBtn.className = 'close-btn';
    closeBtn.onclick = () => document.body.removeChild(overlay);
    
    editorContainer.appendChild(cropButton);
    editorContainer.appendChild(rotateLeftButton);
    editorContainer.appendChild(rotateRightButton);
    editorContainer.appendChild(saveButton);
    
    imageContainer.appendChild(largeImg);
    imageContainer.appendChild(editorContainer);
    
    overlay.appendChild(imageContainer);
    overlay.appendChild(closeBtn);
    document.body.appendChild(overlay);
}

function initCrop(img) {
    if (cropper) {
        cropper.destroy();
    }
    cropper = new Cropper(img, {
        aspectRatio: NaN,
        viewMode: 1,
        minCropBoxWidth: 200,
        minCropBoxHeight: 200,
    });
}

function rotateImage(img, degrees) {
    if (cropper) {
        cropper.rotate(degrees);
    } else {
        img.style.transform = `rotate(${(parseInt(img.dataset.rotation || 0) + degrees) % 360}deg)`;
        img.dataset.rotation = (parseInt(img.dataset.rotation || 0) + degrees) % 360;
    }
}

async function saveEditedImage(img, originalSrc) {
    let editedImageData;
    if (cropper) {
        editedImageData = cropper.getCroppedCanvas().toDataURL();
        cropper.destroy();
        cropper = null;
    } else {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        
        const rotation = parseInt(img.dataset.rotation || 0);
        if (rotation) {
            ctx.save();
            ctx.translate(canvas.width / 2, canvas.height / 2);
            ctx.rotate(rotation * Math.PI / 180);
            ctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2);
            ctx.restore();
        } else {
            ctx.drawImage(img, 0, 0);
        }
        
        editedImageData = canvas.toDataURL();
    }
    
    try {
        const processedImageData = await processImage(editedImageData);
        addPhotoToGallery(processedImageData);
        
        const originalThumbnail = document.querySelector(`img[src="${originalSrc}"]`);
        if (originalThumbnail) {
            originalThumbnail.classList.add('edited');
        }
        
        document.body.removeChild(img.closest('.image-overlay'));
    } catch (error) {
        console.error("Error al procesar la imagen editada:", error);
        speak("Error al procesar la imagen editada");
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
        console.log('Comando detectado:', command);
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

function speak(text, rate = 1, pitch = 1) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    utterance.rate = rate;
    utterance.pitch = pitch;
    
    let voices = speechSynthesis.getVoices();
    let spanishVoice = voices.find(voice => voice.lang.startsWith('es'));
    
    if (spanishVoice) {
        utterance.voice = spanishVoice;
    }
    
    speechSynthesis.speak(utterance);
}

let isProcessing = false;

async function procesarImagenes() {
    console.log("Función procesarImagenes() iniciada");
    
    if (isProcessing) {
        console.log("Ya se está procesando una solicitud. Por favor, espere.");
        return;
    }

    const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
    console.log("Fotos seleccionadas:", fotosSeleccionadas.length);
    
    if (fotosSeleccionadas.length === 0) {
        console.log("No hay fotos seleccionadas");
        alert("Por favor, seleccione al menos una foto para procesar.");
        return;
    }

    isProcessing = true;

    try {
        const formData = new FormData();

        for (let i = 0; i < fotosSeleccionadas.length; i++) {
            const checkbox = fotosSeleccionadas[i];
            const img = checkbox.parentElement.querySelector('img');
            console.log(`Procesando imagen ${i + 1}:`, img.src.substring(0, 50) + "...");

            try {
                const processedImageData = await processImage(img.src);
                const blob = dataURItoBlob(processedImageData.imageData);
                const nombreUUID = generateUUID();
                formData.append('fotos', blob, `${nombreUUID}.png`);
                formData.append('uuid', nombreUUID);
            } catch (error) {
                console.error(`Error al procesar la imagen ${i + 1}:`, error);
                throw error;
            }
        }

        console.log("FormData creado. Preparando para enviar al servidor...");
        console.log("Enviando FormData:", [...formData.entries()].map(([key, value]) => 
            value instanceof File ? `${key}: File(${value.name}, ${value.type}, ${value.size} bytes)` : `${key}: ${value}`
        ));

        const response = await fetch('/upload_fotos', {
            method: 'POST',
            body: formData,
            headers: {
                'HX-Request': 'true'
            }
        });

        if (response.ok) {
            const htmlContent = await response.text();
            document.getElementById('form-section').innerHTML = htmlContent;
            document.getElementById('form-section').style.display = 'block';
            console.log('Imágenes procesadas con éxito');

            // Limpiar fotos procesadas
            fotosSeleccionadas.forEach(checkbox => {
                checkbox.parentElement.remove();
            });

            alert('Imágenes procesadas con éxito');
        } else {
            console.error('Error en la solicitud:', response.status);
            const errorContent = await response.text();
            document.getElementById('form-section').innerHTML = errorContent;
            throw new Error(`HTTP error! status: ${response.status}`);
        }

    } catch (error) {
        console.error('Error al procesar las imágenes:', error);
        alert(`Error al procesar las imágenes: ${error.message}`);
    } finally {
        isProcessing = false;
    }
}

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

// Event listener para el botón de procesar
document.addEventListener('DOMContentLoaded', function() {
    const procesarBtn = document.getElementById('procesarFoto');
    if (procesarBtn) {
        procesarBtn.addEventListener('click', function(event) {
            console.log("Botón 'Procesar' clickeado");
            event.preventDefault();
            
            const userId = localStorage.getItem('authenticatedUserId');
            if (userId) {
                console.log("Usuario autenticado. ID:", userId);
                procesarImagenes();
            } else {
                console.log("Usuario no autenticado");
                alert('Por favor, inicie sesión antes de procesar las imágenes.');
                showAuthModal(); // Asumiendo que esta función existe para mostrar el modal de login
                event.stopImmediatePropagation();
            }
        });
    } else {
        console.error("Botón 'Procesar' no encontrado");
    }
});

// Asignar funciones al objeto global solo si no estamos en un módulo
if (typeof window !== 'undefined') {
    window.toggleCamera = toggleCamera;
    window.capturePhoto = capturePhoto;
    window.toggleVoiceCapture = toggleVoiceCapture;
    window.procesarImagenes = procesarImagenes;
}


async function getCameras() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter(device => device.kind === 'videoinput');
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

console.log("Script camera_functions.js cargado");