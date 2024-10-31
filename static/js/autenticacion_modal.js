// Seleccionar elementos del DOM
const loginBtn = document.getElementById('loginBtn');
const authModal = document.getElementById('authModalContainer');
const authForm = document.getElementById('authForm');
const userInput = document.getElementById('userInput');
const passwordInput = document.getElementById('password');
const forgotPasswordBtn = document.getElementById('forgotPassword');
const changePasswordBtn = document.getElementById('changePassword');

// Mostrar el modal cuando se hace clic en el botón de login
loginBtn.addEventListener('click', () => {
    authModal.style.display = 'block';
});

// Cerrar el modal si se hace clic fuera de él
window.addEventListener('click', (event) => {
  if (event.target === authModal) {
    authModal.style.display = 'none';
  }
});

// Manejar el envío del formulario
authForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const userId = userInput.value;
  const password = passwordInput.value;

  // Aquí iría la lógica de autenticación
  // Por ahora, solo simularemos una autenticación exitosa
  if (userId && password) {
    // Almacenar el ID del usuario en localStorage
    localStorage.setItem('authenticatedUserId', userId);

    // Cerrar el modal
    authModal.style.display = 'none';

    // Limpiar el formulario
    authForm.reset();

    alert('Autenticación exitosa');
    updateLoginButton();
  } else {
    alert('Por favor, ingrese su Email/DNI y contraseña');
    
  }
});

// Función para verificar la autenticación antes de procesar
function checkAuthBeforeProcessing() {
  const authenticatedUserId = localStorage.getItem('authenticatedUserId');
  if (authenticatedUserId) {
    // El usuario está autenticado, proceder con el procesamiento
    // Aquí iría la lógica para procesar
    console.log('Procesando para el usuario:', authenticatedUserId);
    return true;
  } else {
    // El usuario no está autenticado
    alert('Por favor, inicie sesión antes de procesar');
    authModal.style.display = 'block';
    return false;
  }
}

// Agregar el evento al botón de procesar
const procesarBtn = document.getElementById('procesarFoto');
if (procesarBtn) {
  procesarBtn.addEventListener('click', (event) => {
    if (!checkAuthBeforeProcessing()) {
      event.preventDefault();
      event.stopPropagation();
    } else {
      // Aquí iría la lógica de procesamiento
      console.log('Procesando...');
    }
  });
}

// Funcionalidad para los botones de olvidar y cambiar contraseña
forgotPasswordBtn.addEventListener('click', () => {
  alert('Funcionalidad de recuperación de contraseña no implementada');
});

changePasswordBtn.addEventListener('click', () => {
  alert('Funcionalidad de cambio de contraseña no implementada');
});

// Función para actualizar el botón de login/logout
function updateLoginButton() {
  const authenticatedUserId = localStorage.getItem('authenticatedUserId');
  if (authenticatedUserId) {
    loginBtn.textContent = 'Logout';
    loginBtn.removeEventListener('click', showAuthModal);
    loginBtn.addEventListener('click', logout);
  } else {
    loginBtn.textContent = 'Login';
    loginBtn.removeEventListener('click', logout);
    loginBtn.addEventListener('click', showAuthModal);
  }
}

// Función para mostrar el modal de autenticación
function showAuthModal() {
  authModal.style.display = 'block';
}

// Función para cerrar sesión
function logout() {
  localStorage.removeItem('authenticatedUserId');
  updateLoginButton();
  alert('Sesión cerrada');
}

// Actualizar el botón de login/logout al cargar la página
document.addEventListener('DOMContentLoaded', updateLoginButton);

document.addEventListener('DOMContentLoaded', function() {
    const closeBtn = document.getElementById('closeAuthModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            const modal = document.getElementById('authModalContainer');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    }
});