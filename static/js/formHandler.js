// formHandler.js
console.log('Cargando formHandler.js');

let modalInstance = null;

export function initializeFormHandler() {
    console.log('Inicializando manejador de formulario');
    const descartarBtn = document.getElementById('descartar');
    const registrarFotoBtn = document.getElementById('registrarFoto');

    if (descartarBtn) {
        descartarBtn.addEventListener('click', descartarFormulario);
    } else {
        console.error('Botón "descartar" no encontrado');
    }

    if (registrarFotoBtn) {
        registrarFotoBtn.addEventListener('click', registrarFoto);
    } else {
        console.error('Botón "registrarFoto" no encontrado');
    }
}

export function mostrarFormulario() {
    console.log('Mostrando formulario');
    const formSection = document.getElementById('form-section');
    if (formSection) {
        formSection.style.display = 'block';
        setTimeout(() => formSection.classList.add('visible'), 10);
    } else {
        console.error('Sección de formulario no encontrada');
    }
}

function descartarFormulario() {
    console.log('Descartando formulario');
    const formSection = document.getElementById('form-section');
    if (formSection) {
        formSection.classList.remove('visible');
        setTimeout(() => {
            formSection.style.display = 'none';
            limpiarFormulario();
        }, 300);
    } else {
        console.error('Sección de formulario no encontrada');
    }
}

function registrarFoto() {
    console.log('Registrando foto');
    // Aquí iría la lógica para registrar la foto
    alert('Foto registrada con éxito');
    descartarFormulario();
}

function limpiarFormulario() {
    console.log('Limpiando formulario');
    const inputs = document.querySelectorAll('#form-section input');
    inputs.forEach(input => input.value = '');
}

function openFormModal() {
    console.log('Abriendo modal del formulario');
    if (modalInstance) {
        console.log('Modal ya abierto, no se crea uno nuevo');
        return;
    }

    modalInstance = document.createElement('div');
    modalInstance.className = 'modal';
    modalInstance.style.display = 'flex';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    
    const formFields = document.querySelectorAll('#form-section .form-field');
    formFields.forEach(field => {
        const fieldClone = field.cloneNode(true);
        modalContent.appendChild(fieldClone);
    });
    
    const closeBtn = document.createElement('span');
    closeBtn.className = 'close-modal';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = closeFormModal;
    
    modalContent.insertBefore(closeBtn, modalContent.firstChild);
    
    modalInstance.appendChild(modalContent);
    document.body.appendChild(modalInstance);

    document.body.style.overflow = 'hidden';
}

function closeFormModal() {
    if (modalInstance) {
        document.body.removeChild(modalInstance);
        modalInstance = null;
        document.body.style.overflow = 'auto';
    }
}

export { closeFormModal };