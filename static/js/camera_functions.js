// camera_functions.js
import { speak } from './utils.js';
import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';
import { addPhotoToGallery, activarBotones } from './gallery.js';

let isCapturing = false;
let captureCount = 0;
let cameraOn = false;
let recognition;
let isVoiceCaptureActive = false;
let cropper;
let isProcessing = false;
let currentCameraIndex = 0;
let cameras = [];

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
                video: {
                    deviceId: rearCamera ? { exact: rearCamera.deviceId } : undefined,
                    facingMode: rearCamera ? undefined : 'environment',
                    width: { ideal: 4128 },  // 4K
                    height: { ideal: 3096 }, // 4K
                    aspectRatio: { ideal: 4/3 },
                    frameRate: { ideal: 30 }
                }
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
        let tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        document.getElementById('cameraFeed').srcObject = null;
        cameraOn = false;
        speak("Cámara apagada");
    }
}

async function capturePhoto() {
    captureCount++;
    console.log(`Intento de captura #${captureCount}`);
    console.log("Función capturePhoto iniciada");
    console.log("Estado de isCapturing:", isCapturing);
    
    if (isCapturing) {
        console.log("Ya se está capturando una foto. Por favor, espere.");
        return;
    }
    
    if (!cameraOn) {
        console.log("La cámara no está encendida");
        speak("Por favor, enciende la cámara primero.");
        return;
    }

    isCapturing = true;
    console.log("isCapturing establecido a true");

    try {
        console.log("Iniciando captura de imagen");
        const canvas = document.createElement('canvas');
        const video = document.getElementById('cameraFeed');
        // Solo cambiamos estas dos líneas
        canvas.width = 4128;  // En lugar de video.videoWidth
        canvas.height = 3096; // En lugar de video.videoHeight
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);

        console.log("Procesando imagen");
        const { imageData: processedImageData, resized } = await processImage(canvas.toDataURL('image/png'));
        
        console.log('Resolución actual de la cámara:', {
            width: canvas.width,
            height: canvas.height
        });

        alert("Resolución del Dispositivo:  \nAncho:" + canvas.width + "\nAlto: " + canvas.height);

        console.log("Añadiendo foto a la galería");
        await addPhotoToGallery(processedImageData);
        
        speak("Foto capturada");
        console.log("Captura completada con éxito");
    } catch (error) {
        console.error("Error al procesar la imagen:", error);
        speak("Error al procesar la imagen");
        alert("Error al procesar la imagen capturada");
    } finally {
        isCapturing = false;
        console.log("isCapturing restablecido a false");
    }
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
    closeBtn.className = 'close-btnGaleria';
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

async function procesarImagenes() {
    console.log("Función procesarImagenes() iniciada");
    
    if (isProcessing) {
        console.log("Ya se está procesando una solicitud. Por favor, espere.");
        mostrarMensajeModal("Procesamiento en curso, por favor espere", true);
        return;
    }

    const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
    console.log("Fotos seleccionadas:", fotosSeleccionadas.length);
    
    if (fotosSeleccionadas.length === 0) {
        console.log("No hay fotos seleccionadas");
        mostrarMensajeModal("Por favor, seleccione al menos una foto para procesar.", true);
        return;
    }

    isProcessing = true;
    mostrarMensajeModal("Procesando imágenes...", false);

    try {
        const formData = new FormData();

        for (const checkbox of fotosSeleccionadas) {
            const img = checkbox.closest('.miniatura-container').querySelector('img');
            if (!img) continue;

            try {
                // Log del tamaño original
                const originalBlob = await fetch(img.src).then(r => r.blob());
                console.log(`Tamaño original de imagen: ${originalBlob.size / 1024}KB`);

                // Procesar imagen con calidad más baja
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                const tempImg = new Image();
                await new Promise(resolve => {
                    tempImg.onload = resolve;
                    tempImg.src = img.src;
                });

                // Calcular nuevas dimensiones
                let width = tempImg.width;
                let height = tempImg.height;
                const MAX_SIZE = 800; // Reducir más el tamaño máximo

                if (width > MAX_SIZE || height > MAX_SIZE) {
                    const ratio = MAX_SIZE / Math.max(width, height);
                    width *= ratio;
                    height *= ratio;
                }

                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(tempImg, 0, 0, width, height);

                // Convertir a blob con baja calidad
                const blob = await new Promise(resolve => 
                    canvas.toBlob(resolve, 'image/jpeg', 0.6)
                );

                // Log del tamaño después de procesar
                console.log(`Tamaño después de procesar: ${blob.size / 1024}KB`);

                if (blob.size > 1024 * 1024) {
                    throw new Error(`Imagen demasiado grande después de procesar: ${blob.size / 1024}KB`);
                }

                const nombreUUID = generateUUID();
                formData.append('fotos', blob, `${nombreUUID}.jpg`);
                formData.append('uuid', nombreUUID);

            } catch (error) {
                console.error('Error al procesar imagen:', error);
                throw new Error(`Error al procesar una de las imágenes: ${error.message}`);
            }
        }

        console.log("Enviando imágenes al servidor...");
        
        // Log del tamaño total del FormData
        let totalSize = 0;
        for (let pair of formData.entries()) {
            if (pair[1] instanceof Blob) {
                totalSize += pair[1].size;
            }
        }
        console.log(`Tamaño total del FormData: ${totalSize / 1024}KB`);

        const response = await fetch('/upload_fotos', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Respuesta del servidor:', errorText);
            throw new Error(`Error del servidor: ${response.status} - ${errorText}`);
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("text/html")) {
            const htmlContent = await response.text();
            const formSection = document.getElementById('form-section');
            if (formSection) {
                formSection.innerHTML = htmlContent;
                formSection.style.display = 'block';
                console.log('Formulario actualizado y mostrado');
            } else {
                console.error('Elemento form-section no encontrado');
            }

            // Limpiar selección pero mantener las imágenes
            fotosSeleccionadas.forEach(checkbox => {
                checkbox.checked = false;
            });
            activarBotones();
            mostrarMensajeModal('Imágenes procesadas exitosamente', false);
        } else {
            throw new Error('Respuesta del servidor en formato incorrecto');
        }

    } catch (error) {
        console.error('Error al procesar las imágenes:', error);
        mostrarMensajeModal(`Error al procesar las imágenes: ${error.message}`, true);
    } finally {
        isProcessing = false;
    }
}

// Función auxiliar para generar UUID
export function generateUUID() {
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

async function switchCamera() {
    if (!cameraOn) {
        speak("Por favor, enciende la cámara primero.");
        return;
    }

    currentCameraIndex = (currentCameraIndex + 1) % cameras.length;
    toggleCamera();
    toggleCamera();
    speak("Cambiando a la siguiente cámara");
}

// Exportaciones
export { 
    procesarImagenes, 
    toggleCamera, 
    capturePhoto, 
    toggleVoiceCapture, 
    switchCamera,
    showLargeImage
};

// Asignar funciones al objeto global
if (typeof window !== 'undefined') {
    window.toggleCamera = toggleCamera;
    window.capturePhoto = capturePhoto;
    window.toggleVoiceCapture = toggleVoiceCapture;
    window.procesarImagenes = procesarImagenes;
}


//BOTÓN PARA MINIMIZAR VIDEO    *************   BOTÓN PARA MINIMIZAR VIDEO  **********  BOTÓN PARA MINIMIZAR VIDEO
document.getElementById('toggleVisor').addEventListener('click', function() {
    const visor = document.getElementById('camera-visor');
    const icon = this.querySelector('.minimize-icon');
    
    visor.classList.toggle('minimized');
    icon.classList.toggle('minimized');
});

console.log("Script camera_functions.js cargado");