const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const cameraToggle = document.getElementById('cameraToggle');
const cameraFeed = document.getElementById('cameraFeed');
const tomarFotoBtn = document.getElementById('tomarFoto');
const voiceCaptureBtn = document.getElementById('voiceCaptureBtn');
const miniaturas = document.getElementById('miniaturas');
const eliminarFotoBtn = document.getElementById('eliminarFoto');
const guardarFotoBtn = document.getElementById('guardarFoto');
const procesarFotoBtn = document.getElementById('procesarFoto');
let fotosNoGuardadas = false;
let cameraOn = false;
let recognition;

// Botón de login
loginBtn.addEventListener('click', () => {
    alert("Login functionality to be implemented");
});

// Botón de logout con confirmación si hay fotos no guardadas
logoutBtn.addEventListener('click', () => {
    if (fotosNoGuardadas) {
        if (confirm("Hay fotos no guardadas, ¿deseas salir de todas formas?")) {
            alert("Logged out");
        }
    } else {
        alert("Logged out");
    }
});

// Alternar la cámara
cameraToggle.addEventListener('click', () => {
    if (!cameraOn) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                cameraFeed.srcObject = stream;
                cameraOn = true;
                speak("Cámara encendida");
            })
            .catch(err => {
                console.error("Error al encender la cámara: ", err);
                speak("Error al encender la cámara");
            });
    } else {
        let stream = cameraFeed.srcObject;
        let tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        cameraFeed.srcObject = null;
        cameraOn = false;
        speak("Cámara apagada");
    }
});

// Capturar foto (utilizada tanto por el botón como por el comando de voz)
function capturePhoto() {
    if (!cameraOn) {
        speak("Por favor, enciende la cámara primero.");
        return;
    }

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = cameraFeed.videoWidth;
    canvas.height = cameraFeed.videoHeight;
    context.drawImage(cameraFeed, 0, 0, canvas.width, canvas.height);

    const img = document.createElement('img');
    img.src = canvas.toDataURL('image/png');
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
    speak('Foto capturada');
}

tomarFotoBtn.addEventListener('click', capturePhoto);

// Función para mostrar la imagen grande
function showLargeImage(src) {
    const overlay = document.createElement('div');
    overlay.className = 'image-overlay';
    
    const largeImg = document.createElement('img');
    largeImg.src = src;
    largeImg.className = 'large-image';
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'X';
    closeBtn.className = 'close-btn';
    closeBtn.onclick = () => document.body.removeChild(overlay);
    
    overlay.appendChild(largeImg);
    overlay.appendChild(closeBtn);
    document.body.appendChild(overlay);
}

// Activar botones de eliminar, guardar y procesar solo si hay fotos seleccionadas
function activarBotones() {
    const checkboxes = document.querySelectorAll('.fotoCheckbox:checked');
    const activar = checkboxes.length > 0;

    eliminarFotoBtn.disabled = !activar;
    guardarFotoBtn.disabled = !activar;
    procesarFotoBtn.disabled = !activar;
}

// Mostrar la sección al hacer clic en "Procesar"
procesarFotoBtn.addEventListener('click', function() {
    var formSection = document.getElementById('form-section');
    formSection.style.display = 'block';
    setTimeout(function() {
      formSection.classList.add('visible');
    }, 10);
});

// Funcionalidad de Captura por Voz
let isVoiceCaptureActive = false;

voiceCaptureBtn.addEventListener('click', toggleVoiceCapture);

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
    
    // Obtener las voces disponibles
    let voices = speechSynthesis.getVoices();
    
    // Buscar una voz en español
    let spanishVoice = voices.find(voice => voice.lang.startsWith('es'));
    
    // Si se encuentra una voz en español, usarla
    if (spanishVoice) {
        utterance.voice = spanishVoice;
    }
    
    speechSynthesis.speak(utterance);
}

// Listener para los checkboxes de las fotos
miniaturas.addEventListener('change', (event) => {
    if (event.target.classList.contains('fotoCheckbox')) {
        activarBotones();
    }
});

// Funcionalidad para eliminar fotos seleccionadas
eliminarFotoBtn.addEventListener('click', () => {
    const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
    if (fotosSeleccionadas.length === 0) {
        alert("Por favor, seleccione al menos una foto para eliminar.");
        return;
    }
    
    if (confirm(`¿Está seguro de que desea eliminar ${fotosSeleccionadas.length} foto(s)?`)) {
        fotosSeleccionadas.forEach(checkbox => {
            checkbox.parentElement.remove();
        });
        activarBotones();
        speak(`${fotosSeleccionadas.length} foto${fotosSeleccionadas.length > 1 ? 's' : ''} eliminada${fotosSeleccionadas.length > 1 ? 's' : ''}`);
    }
});

// Placeholder para la funcionalidad de guardar fotos
guardarFotoBtn.addEventListener('click', () => {
    alert("Funcionalidad de guardar fotos a implementar");
    fotosNoGuardadas = false;
    activarBotones();
});

// Asegúrate de que los checkboxes activen/desactiven los botones
document.addEventListener('DOMContentLoaded', () => {
    miniaturas.addEventListener('change', (event) => {
        if (event.target.classList.contains('fotoCheckbox')) {
            activarBotones();
        }
    });
});