// utils.js
console.log('Cargando utils.js');

export function initializeUtils() {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const darkModeBtn = document.getElementById('darkModeBtn');

    loginBtn.addEventListener('click', login);
    logoutBtn.addEventListener('click', logout);
    darkModeBtn.addEventListener('click', toggleDarkMode);

    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
        document.body.classList.add('dark-mode');
        darkModeBtn.innerHTML = '☀️';
    }
}

function login() {
    alert("Funcionalidad de login a implementar");
}

function logout() {
    const fotosNoGuardadas = false; // Esta variable debería ser manejada globalmente
    if (fotosNoGuardadas) {
        if (confirm("Hay fotos no guardadas, ¿deseas salir de todas formas?")) {
            alert("Sesión cerrada");
        }
    } else {
        alert("Sesión cerrada");
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
    document.getElementById('darkModeBtn').innerHTML = isDarkMode ? '☀️' : '🌙';
}