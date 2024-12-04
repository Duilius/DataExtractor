class ConnectionToggle {
    constructor() {
        this.button = document.getElementById('toggleConnection');
        this.statusIndicator = document.createElement('span');
        this.initialize();
    }

    initialize() {
        if (!this.button) return;
        
        this.button.appendChild(this.statusIndicator);
        this.updateStatus();

        this.button.addEventListener('click', () => {
            if (sessionManager.isSessionActive()) {
                this.disconnect();
            } else {
                this.connect();
            }
        });
    }

    updateStatus() {
        const isActive = sessionManager.isSessionActive();
        this.statusIndicator.className = isActive ? 'status-connected' : 'status-disconnected';
        this.button.title = isActive ? 'Desconectar' : 'Conectar';
        this.statusIndicator.textContent = isActive ? '⚡ Conectado' : '⭘ Desconectado';
    }

    connect() {
        // Aquí podrías agregar lógica adicional antes de reconectar
        window.location.reload();
    }

    disconnect() {
        sessionManager.logout();
    }

    static init() {
        return new ConnectionToggle();
    }
}