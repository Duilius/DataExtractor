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
    }
}

export function showAuthModal() {
    const authModal = document.getElementById('authModalContainer');
    if (authModal) {
        authModal.style.display = 'block';
    }
}

/* DEL MODAL ANTERIOR
export function showAuthModal() {
    console.log('Intentando mostrar el modal de autenticación');
    const authModal = document.getElementById('authModalContainer');
    console.log('authModal:', authModal);
    if (authModal) {
        authModal.style.display = 'block';
        document.body.classList.add('modal-open');
        console.log('Modal de autenticación mostrado');
    } else {
        console.warn('Elemento authModalContainer no encontrado');
    }
}
*/

export function hideAuthModal() {
    const authModal = document.getElementById('authModalContainer');
    if (authModal) {
        authModal.style.display = 'none';
    }
}

/* DEL MODAL ANTERIOR
export function hideAuthModal() {
    const authModal = document.getElementById('authModalContainer');
    if (authModal) {
        authModal.style.display = 'none';
        document.body.classList.remove('modal-open');
    }
}
*/


function sendEmailsToBackend(visitorEmail, colleagueEmail1, colleagueEmail2) {
    // Implementa aquí la lógica para enviar los emails a tu backend
    console.log('Emails para demo:', visitorEmail, colleagueEmail1, colleagueEmail2);
}

export function checkAuthStatus() {
    return !!localStorage.getItem('visitorEmail');
}


export function handleLogin(e) {
    e.preventDefault();
    const visitorEmail = document.getElementById('visitorEmail').value;
    const colleagueEmail1 = document.getElementById('colleagueEmail1').value;
    const colleagueEmail2 = document.getElementById('colleagueEmail2').value;

    // Almacenar los emails (incluso si están vacíos)
    localStorage.setItem('visitorEmail', visitorEmail);
    localStorage.setItem('colleagueEmail1', colleagueEmail1);
    localStorage.setItem('colleagueEmail2', colleagueEmail2);

    hideAuthModal();
    alert('¡Bienvenido a la demo! Explore las funcionalidades.');
    // Aquí podrías llamar a una función para enviar los emails ingresados a tu backend
    sendEmailsToBackend(visitorEmail, colleagueEmail1, colleagueEmail2);
}


/* DEL MODAL ANTERIOR*/
/*
export function handleLogin(e) {
    e.preventDefault();
    const userInput = document.getElementById('userInput');
    const passwordInput = document.getElementById('password');

    if (!userInput || !passwordInput) {
        console.warn('Elementos de input no encontrados');
        return;
    }

    const userId = userInput.value;
    const password = passwordInput.value;

    // Aquí iría la lógica de autenticación real
    if (userId && password) {
        localStorage.setItem('authenticatedUserId', userId);
        hideAuthModal();
        const authForm = document.getElementById('authForm');
        if (authForm) authForm.reset();
        alert('Autenticación exitosa');
        updateLoginButton();
    } else {
        alert('Por favor, ingrese su Email/DNI y contraseña');
    }
}
*/
function logout() {
    const fotosNoGuardadas = false; // Esta variable debería ser manejada globalmente
    if (fotosNoGuardadas) {
        if (confirm("Hay fotos no guardadas, ¿deseas salir de todas formas?")) {
            performLogout();
        }
    } else {
        performLogout();
    }
}

function performLogout() {
    localStorage.removeItem('authenticatedUserId');
    updateLoginButton();
    alert("Sesión cerrada");
}

function updateLoginButton() {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const authenticatedUserId = localStorage.getItem('authenticatedUserId');

    if (loginBtn && logoutBtn) {
        if (authenticatedUserId) {
            loginBtn.style.display = 'none';
            logoutBtn.style.display = 'inline-block';
        } else {
            loginBtn.style.display = 'inline-block';
            logoutBtn.style.display = 'none';
        }
    } else {
        console.warn('Elementos de botones de login/logout no encontrados');
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

function handleForgotPassword() {
    alert('Funcionalidad de recuperación de contraseña no implementada');
}

function handleChangePassword() {
    alert('Funcionalidad de cambio de contraseña no implementada');
}

export function checkAuthBeforeProcessing() {
    const authenticatedUserId = localStorage.getItem('authenticatedUserId');
    if (authenticatedUserId) {
        return true;
    } else {
        //alert('Por favor, inicie sesión antes de procesar');
        showAuthModal();
        return false;
    }
}


// utils.js - Agregar estas funciones
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

// La función speak que ya tenías
export function speak(text, rate = 1, pitch = 1) {
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
    
    speechSynthesis.cancel(); // Cancelar cualquier síntesis anterior
    speechSynthesis.speak(utterance);
}