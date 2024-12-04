class SessionManager {
    constructor() {
        this.sessionCheckInterval = 5 * 60 * 1000; // 5 minutos
        this.lastActivity = Date.now();
        this.inactivityTimeout = 30 * 60 * 1000;  // 30 minutos de inactividad
        console.log('SessionManager iniciado');
        this.initSessionCheck();
        this.initActivityListeners();
    }

    initSessionCheck() {
        setInterval(() => {
            const inactiveTime = Date.now() - this.lastActivity;
            
            // Solo renovar si hay actividad reciente
            if (inactiveTime < this.inactivityTimeout && this.isSessionValid()) {
                this.renewSession();
            }
        }, this.sessionCheckInterval);
    }

    initActivityListeners() {
        ['click', 'keypress', 'mousemove', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                const now = Date.now();
                // Solo actualizar si han pasado más de 1 minuto desde la última actividad
                if (now - this.lastActivity > 60000) {
                    this.lastActivity = now;
                    if (this.isSessionValid()) {
                        this.renewSession();
                    }
                }
            });
        });
    }

    isSessionValid() {
        const hasSession = document.cookie.includes('session_data=');
        console.log('¿Sesión válida?:', hasSession);
        return hasSession;
    }

    async renewSession() {
        try {
            console.log('Intentando renovar sesión...');
            const response = await fetch('/auth/renew-session', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                console.error('Error renovando sesión:', response.status);
                this.redirectToLogin();
            } else {
                console.log('Sesión renovada exitosamente');
            }
        } catch (error) {
            console.error('Error en la petición de renovación:', error);
            this.redirectToLogin();
        }
    }

    redirectToLogin() {
        console.log('Redirigiendo a login...');
        window.location.href = '/auth/login';
    }
}

// Crear instancia global
const sessionManager = new SessionManager();