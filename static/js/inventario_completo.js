document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const cameraToggle = document.getElementById('cameraToggle');
    const tomarFotoBtn = document.getElementById('tomarFoto');
    const voiceCaptureBtn = document.getElementById('voiceCaptureBtn');
    const miniaturas = document.getElementById('miniaturas');
    const eliminarFotoBtn = document.getElementById('eliminarFoto');
    const guardarFotoBtn = document.getElementById('guardarFoto');
    const procesarFotoBtn = document.getElementById('procesarFoto');
    const subirFotoBtn = document.getElementById('subirFoto');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const formSection = document.getElementById('form-section');

    let fotosNoGuardadas = false;
    let cameraOn = false;
    let recognition;
    let isVoiceCaptureActive = false;
    let cropper;

    loginBtn.addEventListener('click', () => {
        alert("Login functionality to be implemented");
    });

    logoutBtn.addEventListener('click', () => {
        if (fotosNoGuardadas) {
            if (confirm("Hay fotos no guardadas, ¿deseas salir de todas formas?")) {
                alert("Logged out");
            }
        } else {
            alert("Logged out");
        }
    });

    cameraToggle.addEventListener('click', toggleCamera);
    tomarFotoBtn.addEventListener('click', capturePhoto);
    voiceCaptureBtn.addEventListener('click', toggleVoiceCapture);
    miniaturas.addEventListener('change', (event) => {
        if (event.target.classList.contains('fotoCheckbox')) {
            activarBotones();
        }
    });
    eliminarFotoBtn.addEventListener('click', eliminarFotosSeleccionadas);
    guardarFotoBtn.addEventListener('click', mostrarOpcionesGuardado);
    procesarFotoBtn.addEventListener('click', mostrarFormularioProcesamiento);
    subirFotoBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '#e9e9e9';
    });
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '';
        handleFiles(e.dataTransfer.files);
    });

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

    function capturePhoto() {
        if (!cameraOn) {
            speak("Por favor, enciende la cámara primero.");
            return;
        }

        const canvas = document.createElement('canvas');
        const video = document.getElementById('cameraFeed');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);

        addPhotoToGallery(canvas.toDataURL('image/png'));
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
        miniaturas.appendChild(miniaturaContainer);

        fotosNoGuardadas = true;
        activarBotones();
        speak('Foto añadida a la galería');
    }


// Agregar el botón de modo oscuro
const darkModeBtn = document.createElement('button');
darkModeBtn.id = 'darkModeBtn';
darkModeBtn.className = 'btn';
darkModeBtn.innerHTML = '🌙';
darkModeBtn.onclick = toggleDarkMode;
document.getElementById('header-content').appendChild(darkModeBtn);

    // Inicializar el modo oscuro según la preferencia guardada
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
        document.body.classList.add('dark-mode');
        darkModeBtn.innerHTML = '☀️';
    }

    function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
        darkModeBtn.innerHTML = isDarkMode ? '☀️' : '🌙';
    }


    function showLargeImage(src) {
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
        rotateLeftButton.onclick = () => rotateImage(-90);
        
        const rotateRightButton = document.createElement('button');
        rotateRightButton.textContent = 'Rotar Derecha';
        rotateRightButton.onclick = () => rotateImage(90);
        
        const zoomInButton = document.createElement('button');
        zoomInButton.textContent = 'Zoom In';
        zoomInButton.onclick = () => zoomImage(0.1);
        
        const zoomOutButton = document.createElement('button');
        zoomOutButton.textContent = 'Zoom Out';
        zoomOutButton.onclick = () => zoomImage(-0.1);
        
        const saveButton = document.createElement('button');
        saveButton.textContent = 'Guardar Cambios';
        saveButton.onclick = () => saveEditedImage(src);
        
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'X';
        closeBtn.className = 'close-btn';
        closeBtn.onclick = () => {
            if (cropper) {
                cropper.destroy();
            }
            document.body.removeChild(overlay);
        };
        
        editorContainer.appendChild(cropButton);
        editorContainer.appendChild(rotateLeftButton);
        editorContainer.appendChild(rotateRightButton);
        editorContainer.appendChild(zoomInButton);
        editorContainer.appendChild(zoomOutButton);
        editorContainer.appendChild(saveButton);
        
        imageContainer.appendChild(largeImg);
        overlay.appendChild(imageContainer);
        overlay.appendChild(editorContainer);
        overlay.appendChild(closeBtn);
        document.body.appendChild(overlay);
        
        initCrop(largeImg);
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
            ready: function() {
                this.cropper.crop();
            }
        });
    }

    function rotateImage(degree) {
        if (cropper) {
            cropper.rotate(degree);
        }
    }

    function zoomImage(ratio) {
        if (cropper) {
            cropper.zoom(ratio);
        }
    }


    function saveEditedImage(originalSrc) {
        if (cropper) {
            const canvas = cropper.getCroppedCanvas();
            const editedImageData = canvas.toDataURL('image/png');
            addPhotoToGallery(editedImageData);
            
            const originalThumbnail = document.querySelector(`img[src="${originalSrc}"]`);
            if (originalThumbnail) {
                originalThumbnail.classList.add('edited');
            }
            
            cropper.destroy();
            document.body.removeChild(document.querySelector('.image-overlay'));
        }
    }

    // Función para cambiar entre modo claro y oscuro
    function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
        updateDarkModeButton(isDarkMode);
    }

    function updateDarkModeButton(isDarkMode) {
        const darkModeBtn = document.getElementById('darkModeBtn');
        darkModeBtn.innerHTML = isDarkMode ? '☀️' : '🌙';
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
        voiceCaptureBtn.textContent = 'Detener Captura por Voz';
        speak('Captura por voz activada. Diga "tomar foto" o "capturar" en cualquier momento para tomar una foto.');
    }

    function stopVoiceCapture() {
        if (recognition) {
            recognition.stop();
            recognition.onend = null;
            recognition = null;
        }
        isVoiceCaptureActive = false;
        voiceCaptureBtn.textContent = 'Foto por Voz';
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

    function activarBotones() {
        const checkboxes = document.querySelectorAll('.fotoCheckbox:checked');
        const activar = checkboxes.length > 0;
        eliminarFotoBtn.disabled = !activar;
        guardarFotoBtn.disabled = !activar;
        procesarFotoBtn.disabled = !activar;
    }

    function eliminarFotosSeleccionadas() {
        const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
        if (fotosSeleccionadas.length === 0) {
            alert("Por favor, seleccione al menos una foto para eliminar.");
            return;
        }
        
        if (confirm(`¿Está seguro de que desea eliminar ${fotosSeleccionadas.length} foto(s)?`)) {
            fotosSeleccionadas.forEach(checkbox => checkbox.parentElement.remove());
            activarBotones();
            speak(`${fotosSeleccionadas.length} foto${fotosSeleccionadas.length > 1 ? 's' : ''} eliminada${fotosSeleccionadas.length > 1 ? 's' : ''}`);
        }
    }

    function mostrarOpcionesGuardado() {
        const options = ["Guardar en Drive", "Guardar en Servidor", "Guardar en Local"];
        const selectedOption = prompt(`Seleccione una opción de guardado:\n1. ${options[0]}\n2. ${options[1]}\n3. ${options[2]}\n\nIngrese el número de la opción:`);

        switch(selectedOption) {
            case "1": guardarEnDrive(); break;
            case "2": guardarEnServidor(); break;
            case "3": guardarEnLocal(); break;
            default: alert("Opción no válida o cancelada.");
        }
    }

    function guardarEnDrive() {
        alert("Función guardarEnDrive no implementada");
    }

    function guardarEnServidor() {
        alert("Función guardarEnServidor no implementada");
    }

    function guardarEnLocal() {
        alert("Función guardarEnLocal no implementada");
    }

    function mostrarFormularioProcesamiento() {
        formSection.style.display = 'block';
        setTimeout(() => formSection.classList.add('visible'), 10);
        procesarImagenes();
    }

    async function procesarImagenes() {
        const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
        if (fotosSeleccionadas.length === 0) {
            alert("Por favor, seleccione al menos una foto para procesar.");
            return;
        }

        const formData = new FormData();

        fotosSeleccionadas.forEach((checkbox, index) => {
            const img = checkbox.parentElement.querySelector('img');
            const blob = dataURItoBlob(img.src);
            formData.append('fotos', blob, `foto${index}.png`);
        });

        try {
            const response = await fetch('/upload_fotos', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            const result = await response.json();
            console.log('Resultado del procesamiento:', result);
            alert('Imágenes procesadas con éxito');
            
            fotosSeleccionadas.forEach(checkbox => {
                checkbox.parentElement.remove();
            });
            activarBotones();
        } catch (error) {
            console.error('Error al procesar las imágenes:', error);
            alert(`Error al procesar las imágenes: ${error.message}`);
        }
    }

    function handleFileSelect(e) {
        handleFiles(e.target.files);
    }

    function handleFiles(files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => addPhotoToGallery(e.target.result);
                reader.readAsDataURL(file);
            }
        });
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
});