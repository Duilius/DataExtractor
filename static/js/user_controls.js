document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    function updateButtons() {
        const hasSession = document.cookie.includes('session_data=');
        loginBtn.style.display = hasSession ? 'none' : 'block';
        logoutBtn.style.display = hasSession ? 'block' : 'none';
    }

    // Actualizar botones inicialmente
    updateButtons();

    // Actualizar cada 5 segundos
    setInterval(updateButtons, 5000);

    loginBtn.addEventListener('click', () => {
        window.location.href = '/auth/login';
    });

    logoutBtn.addEventListener('click', async () => {
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } finally {
            window.location.href = '/auth/login';
        }
    });
});