// formHandler.js
import { mostrarMensajeModal } from './utils.js';
export { 
    //limpiarFormulario, 
    mostrarMensajeModal,
    //initializeFormHandler, 
    //mostrarFormulario, 
    closeFormModal 
};
console.log('Cargando formHandler.js');

let modalInstance = null;

export function initializeFormHandler() {
    console.log('Inicializando manejador de formulario');
    const descartarBtn = document.getElementById('descartarData');
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
/*
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
*/
function registrarFoto() {
    console.log('Registrando foto');
    // Aquí iría la lógica para registrar la foto
    //alert('Foto registrada con éxito');
    //descartarFormulario();
    return true;
}

// Modificar esta función para que solo limpie cuando se le indique
// En formHandler.js

export function limpiarFormulario() {
    console.log('Limpiando formulario');
    const formSection = document.getElementById('form-section');
    if (!formSection) return;

    // Limpiar todos los inputs excepto los hidden
    const inputs = formSection.querySelectorAll('input:not([type="hidden"])');
    inputs.forEach(input => {
        input.value = '';
        input.classList.remove('error', 'highlight');
    });

    // Limpiar selects
    const estado = document.getElementById('estado');
    if (estado) {
        estado.selectedIndex = 0;
        estado.classList.remove('error');
    }

    // Limpiar radio buttons de En Uso
    const radioButtons = document.querySelectorAll('input[name="enUso"]');
    radioButtons.forEach(radio => {
        radio.checked = false;
    });
    const radioGroup = document.querySelector('.radio-group');
    if (radioGroup) {
        radioGroup.classList.remove('error');
    }

    // Limpiar galería de imágenes
    const miniaturas = document.getElementById('miniaturas');
    if (miniaturas) {
        miniaturas.innerHTML = '';
    }

    // Desactivar botones relacionados con las fotos
    ['eliminarFoto', 'guardarFoto', 'procesarFoto'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.disabled = true;
        }
    });

    // Mantener el formulario visible
    formSection.style.display = 'block';
}

// Modificar la función descartarFormulario para que no oculte el formulario
function descartarFormulario() {
    console.log('Descartando formulario');
    limpiarFormulario();
    mostrarMensajeModal('Formulario descartado', false);
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
