// utils.js
export function initializeUtils() {
    const darkModeBtn = document.getElementById('darkModeBtn');
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', toggleDarkMode);
    }

    // Inicializar modal
    const closeModal = document.getElementById("closeModal");
    if (closeModal) {
        closeModal.onclick = function() {
            document.getElementById("errorModal").style.display = "none";
        };
    }

    // Cargar preferencia de modo oscuro
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
        document.body.classList.add('dark-mode');
        if (darkModeBtn) darkModeBtn.innerHTML = '☀️';
    }
}

export function speak(text, rate = 1, pitch = 1) {
    // Si la síntesis de voz no está disponible
    if (!window.speechSynthesis) {
        console.error('La síntesis de voz no está disponible en este navegador');
        return;
    }

    // Crear una nueva utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    utterance.rate = rate;
    utterance.pitch = pitch;
    
    // Si las voces aún no están cargadas
    if (window.speechSynthesis.getVoices().length === 0) {
        window.speechSynthesis.addEventListener('voiceschanged', () => {
            asignarVozYHablar(utterance);
        }, { once: true });
    } else {
        asignarVozYHablar(utterance);
    }
}

function asignarVozYHablar(utterance) {
    const voices = window.speechSynthesis.getVoices();
    const spanishVoice = voices.find(voice => 
        voice.lang.startsWith('es') || 
        voice.name.toLowerCase().includes('spanish')
    );
    
    if (spanishVoice) {
        utterance.voice = spanishVoice;
    }
    
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    console.log(`Hablando: "${utterance.text}" con voz: ${utterance.voice?.name || 'default'}`);
}

export function initializeVoice() {
    if ('speechSynthesis' in window) {
        speechSynthesis.getVoices();
        setTimeout(() => {
            speak('Sistema de lectura de códigos inicializado', 1, 1);
        }, 1000);
    } else {
        console.error('La síntesis de voz no está soportada en este navegador');
    }
}

export function mostrarMensajeModal(mensaje, esError = false) {
    const modal = document.getElementById("errorModal");
    const modalContent = document.getElementById("errorMessage");
    
    if (modalContent) {
        modalContent.textContent = mensaje;
        modalContent.style.color = esError ? '#dc3545' : '#28a745';
    }
    
    if (modal) {
        modal.style.display = "flex";
        speak(mensaje);
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
    
    const darkModeBtn = document.getElementById('darkModeBtn');
    if (darkModeBtn) {
        darkModeBtn.innerHTML = isDarkMode ? '☀️' : '🌙';
    }
}