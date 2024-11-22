// utils.js
console.log('Cargando utils.js');

export function initializeUtils() {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const darkModeBtn = document.getElementById('darkModeBtn');

    if (loginBtn) {
        loginBtn.addEventListener('click', showAuthModal);
    } else {
        console.warn('Elemento loginBtn no encontrado');
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    } else {
        console.warn('Elemento logoutBtn no encontrado');
    }

    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', toggleDarkMode);
    } else {
        console.warn('Elemento darkModeBtn no encontrado');
    }

    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
        document.body.classList.add('dark-mode');
        if (darkModeBtn) darkModeBtn.innerHTML = '☀️';
    }

    updateLoginButton();
}

export function initializeAuthModal() {
    const authModal = document.getElementById('authModalContainer');
    const closeBtn = document.getElementById('closeAuthModal');
    const authForm = document.getElementById('authForm');

    if (closeBtn) {
        closeBtn.addEventListener('click', hideAuthModal);
    }

    if (authModal) {
        window.addEventListener('click', (event) => {
            if (event.target === authModal) {
                hideAuthModal();
            }
        });
    }

    if (authForm) {
        authForm.addEventListener('submit', handleLogin);
    } else {
        console.warn('Formulario de autenticación no encontrado');
    }

    // Restablecer valores guardados si existen
    const visitorEmail = localStorage.getItem('visitorEmail');
    const colleagueEmail1 = localStorage.getItem('colleagueEmail1');
    const colleagueEmail2 = localStorage.getItem('colleagueEmail2');

    if (visitorEmail) {
        const visitorInput = document.getElementById('visitorEmail');
        if (visitorInput) visitorInput.value = visitorEmail;
    }
    if (colleagueEmail1) {
        const colleague1Input = document.getElementById('colleagueEmail1');
        if (colleague1Input) colleague1Input.value = colleagueEmail1;
    }
    if (colleagueEmail2) {
        const colleague2Input = document.getElementById('colleagueEmail2');
        if (colleague2Input) colleague2Input.value = colleagueEmail2;
    }
}

export function showAuthModal() {
    const authModal = document.getElementById('authModalContainer');
    if (authModal) {
        authModal.style.display = 'block';
        // Agregar botón para continuar sin autenticación
        const skipButton = document.createElement('button');
        skipButton.textContent = 'Continuar sin registrarse';
        skipButton.onclick = () => {
            authModal.style.display = 'none';
        };
        const modalContent = authModal.querySelector('.modal-content');
        if (modalContent && !modalContent.querySelector('.skip-button')) {
            modalContent.appendChild(skipButton);
        }
    }
}

export function hideAuthModal() {
    const authModal = document.getElementById('authModalContainer');
    if (authModal) {
        authModal.style.display = 'none';
    }
}

function updateLoginButton() {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const isAuthenticated = checkAuthStatus();

    if (loginBtn && logoutBtn) {
        if (isAuthenticated) {
            loginBtn.style.display = 'none';
            logoutBtn.style.display = 'inline-block';
        } else {
            loginBtn.style.display = 'inline-block';
            logoutBtn.style.display = 'none';
        }
    }
}

export function checkAuthStatus() {
    return !!localStorage.getItem('visitorEmail');
}

export function checkAuthBeforeProcessing() {
    const isAuthenticated = localStorage.getItem('visitorEmail');
    if (!isAuthenticated) {
        // Solo mostramos el modal como sugerencia
        showAuthModal();
    }
    // Siempre retornamos true para permitir continuar
    return true;
}

export function handleLogin(e) {
    e.preventDefault();
    
    const visitorEmail = document.getElementById('visitorEmail')?.value;
    const colleagueEmail1 = document.getElementById('colleagueEmail1')?.value;
    const colleagueEmail2 = document.getElementById('colleagueEmail2')?.value;

    if (!visitorEmail) {
        mostrarMensajeModal('Por favor ingrese su email', true);
        return;
    }

    // Almacenar los emails
    localStorage.setItem('visitorEmail', visitorEmail);
    if (colleagueEmail1) localStorage.setItem('colleagueEmail1', colleagueEmail1);
    if (colleagueEmail2) localStorage.setItem('colleagueEmail2', colleagueEmail2);

    // Enviar emails al backend
    sendEmailsToBackend(visitorEmail, colleagueEmail1, colleagueEmail2);

    hideAuthModal();
    updateLoginButton();
    mostrarMensajeModal('¡Bienvenido a la demo! Explore las funcionalidades.', false);
}

function logout() {
    const fotosNoGuardadas = document.querySelectorAll('.miniatura-container').length > 0;
    
    if (fotosNoGuardadas) {
        if (confirm("Hay fotos no guardadas, ¿deseas salir de todas formas?")) {
            performLogout();
        }
    } else {
        performLogout();
    }
}

function performLogout() {
    localStorage.removeItem('visitorEmail');
    localStorage.removeItem('colleagueEmail1');
    localStorage.removeItem('colleagueEmail2');
    updateLoginButton();
    mostrarMensajeModal("Sesión cerrada", false);
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

function sendEmailsToBackend(visitorEmail, colleagueEmail1, colleagueEmail2) {
    fetch('/register_emails', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            visitorEmail,
            colleagueEmail1,
            colleagueEmail2
        })
    })
    .then(response => response.json())
    .catch(error => console.error('Error al registrar emails:', error));
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
        
        // Cerrar automáticamente después de 3 segundos
        setTimeout(() => {
            modal.style.display = "none";
        }, 3000);
    } else {
        console.warn('Modal de mensajes no encontrado');
        alert(mensaje); // Fallback si no existe el modal
    }
}

export function speak(text, rate = 1, pitch = 1) {
    if (!window.speechSynthesis) {
        console.warn('Síntesis de voz no soportada en este navegador');
        return;
    }

    // Cancelar cualquier síntesis anterior
    window.speechSynthesis.cancel();

    // Esperar a que las voces estén cargadas
    if (speechSynthesis.getVoices().length === 0) {
        speechSynthesis.addEventListener('voiceschanged', () => {
            realizarHabla(text, rate, pitch);
        }, { once: true });
    } else {
        realizarHabla(text, rate, pitch);
    }
}

function realizarHabla(text, rate = 1, pitch = 1) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    utterance.rate = rate;
    utterance.pitch = pitch;
    
    const voices = speechSynthesis.getVoices();
    const spanishVoice = voices.find(voice => voice.lang.startsWith('es'));
    
    if (spanishVoice) {
        utterance.voice = spanishVoice;
    }
    
    speechSynthesis.speak(utterance);
}

// Hacer funciones disponibles globalmente
window.speak = speak;
window.mostrarMensajeModal = mostrarMensajeModal;
window.toggleDarkMode = toggleDarkMode;