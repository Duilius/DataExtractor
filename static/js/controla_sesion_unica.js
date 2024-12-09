// Agregar al base_auth.html o en un archivo js separado
document.body.addEventListener('htmx:afterSettle', function(evt) {
    if (evt.detail.triggerSpec === "check-single-session") {
        // Verificar sesión cada 30 segundos
        setInterval(checkSession, 30000);
    }
});

async function checkSession() {
    try {
        const response = await fetch('/auth/session-info');
        const data = await response.json();
        
        if (!data.authenticated) {
            // Sesión inválida, redirigir a login
            window.location.href = '/auth/login';
        }
    } catch (error) {
        console.error('Error verificando sesión:', error);
    }
}

// Broadcast channel para comunicación entre pestañas
const channel = new BroadcastChannel('auth_channel');

channel.onmessage = (event) => {
    if (event.data === 'logout') {
        window.location.href = '/auth/login';
    }
};

// Al hacer login exitoso
channel.postMessage('logout'); // Cierra otras sesiones