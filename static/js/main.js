import { speak } from './utils.js';

console.log('Cargando main.js');
import { limpiarFormulario } from './formHandler.js';
import { mostrarMensajeModal } from './utils.js';

import { procesarImagenes, toggleCamera, capturePhoto, toggleVoiceCapture } from './camera_functions.js';
import { initializeCamera } from './camera.js';
import { initializeGallery, activarBotones } from './gallery.js';
import { initializeImageEditor } from './imageEditor.js';
import { initializeFormHandler, mostrarFormulario } from './formHandler.js';
import { initializeUtils, initializeAuthModal, checkAuthBeforeProcessing, showAuthModal, checkAuthStatus } from './utils.js';
import { initializeSearch } from './search.js';
import { initializeWorkerInfo } from './worker_info.js';
import './imageProcessor.js';

window.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM completamente cargado en main.js');
    
    /*
    if (!checkAuthStatus()) {
        showAuthModal();
    }
    */
    initializeCamera();
    initializeGallery();
    initializeImageEditor();
    initializeFormHandler();
    initializeUtils();
    initializeSearch();
    initializeWorkerInfo();

    // Configurar el evento click para el botón de login
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', showAuthModal);
    } else {
        console.warn('Botón de login no encontrado');
    }

     // Manejar el cierre del modal principal
     const modal = document.getElementById('modal');
     const closeBtn = document.querySelector('.close');
 
     if (closeBtn) {
         closeBtn.onclick = function() {
             modal.style.display = "none";
         }
     }
 
     window.onclick = function(event) {
         if (event.target == modal) {
             modal.style.display = "none";
         }
     }


    // Hacer procesarImagenes disponible globalmente
    window.procesarImagenes = procesarImagenes;

    // Cargar el contenido del modal de autenticación
    fetch('templates/demo/autenticacion_modal2.html')
    .then(response => response.text())
    .then(html => {
        const modalContainer = document.getElementById('authModalContainer');
        if (modalContainer) {
            modalContainer.innerHTML = html;
            initializeAuthModal();
        } else {
            console.warn('Contenedor del modal de autenticación no encontrado');
        }
    })
    .catch(error => console.error('Error al cargar el modal de autenticación:', error));

    // Modificar el comportamiento del botón "Procesar"
    const procesarBtn = document.getElementById('procesarFoto');
    if (procesarBtn) {
        procesarBtn.addEventListener('click', () => {
            if (checkAuthBeforeProcessing()) {
                procesarImagenes();
            }
        });
    } else {
        console.warn('Botón de procesar no encontrado');
    }
});

// Función global para cerrar el modal principal
window.closeModal = function() {
    document.getElementById('modal').style.display = "none";
}



    // Cargar el contenido del modal de autenticación
    /*
    fetch('templates/demo/autenticacion_modal.html')
    .then(response => response.text())
    .then(html => {
        const modalContainer = document.getElementById('authModalContainer');
        if (modalContainer) {
            modalContainer.innerHTML = html;
            initializeAuthModal();
        } else {
            console.warn('Contenedor del modal de autenticación no encontrado');
        }
    })
    .catch(error => console.error('Error al cargar el modal de autenticación:', error));

    */

    // Modificar el comportamiento del botón "Procesar"
    const procesarBtn = document.getElementById('procesarFoto');
    if (procesarBtn) {
        procesarBtn.addEventListener('click', () => {
            if (checkAuthBeforeProcessing()) {
                procesarImagenes();
            }
        });
    } else {
        console.warn('Botón de procesar no encontrado');
    }


/*FUNCIONALIDADES VALIDAR FORMULARIO DE REGISTRO/INSERCIÓN*/

// Contador de registros exitosos
let registrosExitosos = parseInt(localStorage.getItem('registrosExitosos') || '0');

// Mostrar barra de progreso
function mostrarBarraProgreso() {
    const barraProgreso = document.createElement('div');
    barraProgreso.id = 'barraProgreso';
    barraProgreso.innerHTML = `
        <div class="progreso">
            <div class="fuego"></div>
        </div>
        <div class="contador">5</div>
    `;
    document.body.appendChild(barraProgreso);

    let segundos = 5;
    const intervalo = setInterval(() => {
        segundos--;
        document.querySelector('#barraProgreso .contador').textContent = segundos;
        document.querySelector('#barraProgreso .fuego').style.width = `${(5 - segundos) * 20}%`;
        if (segundos === 0) {
            clearInterval(intervalo);
            barraProgreso.remove();
        }
    }, 1000);
}



// Definir campos obligatorios globalmente
const camposObligatorios = [
    { id: 'institucion', tipo: 'input' },
    { id: 'worker', tipo: 'input' },
    { id: 'registrador', tipo: 'input' },
    { id: 'cod-2024', tipo: 'input' },
    { id: 'color', tipo: 'input' },
    { id: 'descripcion', tipo: 'input' },
    { id: 'estado', tipo: 'select' }
 ];
 
 // Función para validar el formulario
 function validarFormulario() {
    console.log("Iniciando validación");
    let valido = true;
    let errores = [];
 
    // Validar campos de texto, select y párrafo
    camposObligatorios.forEach(campo => {
        const elemento = document.querySelector(`#${campo.id}`);
        if (!elemento) {
            console.log(`Elemento ${campo.id} no encontrado`);
            valido = false;
            errores.push(`Campo ${campo.id} no encontrado`);
            return;
        }
 
        let valor = campo.tipo === 'input' || campo.tipo === 'select' ? 
                   elemento.value : 
                   elemento.textContent;
 
        console.log(`Verificando campo ${campo.id}:`, {
            tipo: campo.tipo,
            valor: valor,
            elemento: elemento
        });
 
        if (!valor || 
            valor.trim() === '' || 
            valor === 'No disponible' || 
            valor === 'Nombre del Trabajador') {
            valido = false;
            console.log(`Campo ${campo.id} vacío o no válido`);
            elemento.classList.add('error');
            errores.push(`Campo ${campo.id} es obligatorio`);
        } else {
            elemento.classList.remove('error');
        }
    });
 
    // Validar radio button de En Uso
    const enUsoChecked = document.querySelector('input[name="enUso"]:checked');
    if (!enUsoChecked) {
        valido = false;
        console.log("En uso no seleccionado");
        const radioGroup = document.querySelector('.radio-group:has(input[name="enUso"])');
        if (radioGroup) {
            radioGroup.classList.add('error');
        }
        errores.push("Debe indicar si el bien está en uso");
    }
 
    if (!valido) {
        document.getElementById('form-section').style.display = 'block';
        alert(errores[0]); // Mostrar solo el primer error encontrado
        return false;
    }
 
    // Validación de formato de código de inventario
    const cod2024 = document.querySelector('#cod-2024').value;
    if (!/^\d+(-\d+)?$/.test(cod2024)) {
        document.querySelector('#cod-2024').classList.add('error');
        document.getElementById('form-section').style.display = 'block';
        alert("El código de inventario debe ser numérico y puede contener un guion");
        return false;
    }
 
    // Validación condicional para muebles
    const descripcion = document.querySelector('#descripcion').value.toLowerCase();
    const muebles = ['escritorio', 'mueble', 'mesa', 'repostero', 'estante', 
                     'archivador', 'credenza', 'pizarra', 'armario', 'librero', 
                     'persiana', 'cortina'];
    
    if (muebles.some(mueble => descripcion.includes(mueble))) {
        const medidas = ['largo', 'alto', 'ancho'];
        const medidasVacias = medidas.some(medida => !document.querySelector(`#${medida}`)?.value);
        
        if (medidasVacias) {
            if (confirm('Este tipo de bien requiere medidas. ¿Desea agregarlas ahora?')) {
                medidas.forEach(medida => {
                    const inputMedida = document.querySelector(`#${medida}`);
                    if (inputMedida && !inputMedida.value) {
                        inputMedida.classList.add('highlight');
                    }
                });
                return false;
            }
        } else {
            medidas.forEach(medida => {
                const inputMedida = document.querySelector(`#${medida}`);
                if (inputMedida) {
                    inputMedida.classList.remove('highlight');
                }
            });
        }
    }
 
    return valido;
 }
 
 // Event listeners
 document.addEventListener('DOMContentLoaded', function() {
    // Event listeners para campos
    camposObligatorios.forEach(campo => {
        const input = document.querySelector(`#${campo.id}`);
        if (input) {
            input.addEventListener('input', function() {
                if (this.value.trim() && this.value !== "No disponible") {
                    this.classList.remove('error');
                }
            });
        }
    });
 
    // Event listener para el botón registrar
    const registrarBtn = document.getElementById('registrarFoto');
    if (registrarBtn) {
        registrarBtn.addEventListener('click', function() {
            console.log("Botón registrar clickeado");
            registrarBien();
        });
    }
 });
 
 // Función para registrar el bien
 async function registrarBien() {
    console.log("Iniciando proceso de registro");
    
    if (!validarFormulario()) {
        console.log("Validación fallida");
        return;
    }

    try {
        console.log("Preparando datos del formulario");
        const formData = new FormData();

        // Mapeo de campos a sus selectores
        const campos = {
            'institucion': '#institucion',
            'worker': '#worker',
            'registrador': '#registrador',
            'cod_patr': '#cod-patr',
            'cod_2024': '#cod-2024',
            'cod_2023': '#cod-2023',
            'cod_2021': '#cod-2021',
            'cod_2019': '#cod-2019',
            'color': '#color',
            'material': '#material',
            'largo': '#largo',
            'ancho': '#ancho',
            'alto': '#alto',
            'marca': '#marca',
            'modelo': '#modelo',
            'num_serie': '#num-serie',
            'descripcion': '#descripcion',
            'observaciones': '#observaciones'
        };
        
        // Agregar cada campo al FormData
        for (const [key, selector] of Object.entries(campos)) {
            const elemento = document.querySelector(selector);
            let valor = elemento ? elemento.value : '';
            formData.append(key, valor);
        }

        const enUso = document.querySelector('input[name="enUso"]:checked')?.value || 'No';
        formData.append('enUso', enUso);

        const estado = document.querySelector('#estado')?.value || '';
        formData.append('estado', estado);

        console.log("Enviando datos al servidor...");
        
        const response = await fetch('/registrar_bien', {
            method: 'POST',
            body: formData
        });

        const contentType = response.headers.get("content-type");

        // Procesar respuesta JSON o HTML según el tipo de contenido
        if (contentType && contentType.includes("application/json")) {
            const data = await response.json();
            if (response.ok && data.exito) {
                //alert('Registro completado con éxito');
                mostrarMensajeModal('Registro completado con éxito', false);
                limpiarFormulario();
            } else {
                //mostrarErrorModal(data.error || 'Error en el registro');
                mostrarMensajeModal(data.error || 'Error en el registro', true);
            }
        } else {
            const errorHtml = await response.text();
            //mostrarErrorModal("Ocurrió un error: revise los campos e intente nuevamente.");
            mostrarMensajeModal("Ocurrió un error: revise los campos e intente nuevamente.", true);
        }

    } catch (error) {
        console.error('Error:', error);
        //mostrarErrorModal('Error al procesar el registro: ' + error.message);
        mostrarMensajeModal('Error al procesar el registro: ' + error.message, true);
    }
}

// Actualizar el event listener para el botón descartar
document.addEventListener('DOMContentLoaded', function() {
    const descartarBtn = document.getElementById('descartarData');
    if (descartarBtn) {
        descartarBtn.addEventListener('click', function() {
            limpiarFormulario();
            // Asegurar que el formulario permanezca visible
            const formSection = document.getElementById('form-section');
            if (formSection) {
                formSection.style.display = 'block';
            }
            mostrarMensajeModal('Formulario descartado', false);
        });
    }

// Función para mostrar el modal de error
function mostrarErrorModal(mensaje) {
    const modal = document.getElementById("errorModal");
    const modalContent = document.getElementById("errorMessage");
    modalContent.textContent = mensaje;
    modal.style.display = "flex";
}

// Cerrar el modal al hacer clic en el botón de cerrar
document.getElementById("closeModal").onclick = function () {
    document.getElementById("errorModal").style.display = "none";
};

 
 function solicitarEnvioReporte() {
    if (confirm('¿Desea recibir un reporte de los bienes registrados?')) {
        fetch('/enviar_reporte', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.enviado) {
                    alert('El reporte ha sido enviado a su correo');
                } else {
                    alert('Hubo un error al enviar el reporte');
                }
            })
            .catch(error => console.error('Error:', error));
    }
 }

// Función para hablar mensajes
function hablarMensaje(mensaje) {
    const voces = speechSynthesis.getVoices().filter(voz => voz.lang.startsWith('es'));
    const vozAleatoria = voces[Math.floor(Math.random() * voces.length)];
    const utterance = new SpeechSynthesisUtterance(mensaje);
    utterance.voice = vozAleatoria;
    speechSynthesis.speak(utterance);
}

});
// Manejar el modal de autenticación
/*
function manejarModalAutenticacion() {
    const modal = document.getElementById('authModalContainer');
    const form = document.getElementById('authForm');
    const closeBtn = document.getElementById('closeAuthModal');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const userEmail = document.getElementById('userEmail').value;
        const colleagueEmail1 = document.getElementById('colleagueEmail1').value;
        const colleagueEmail2 = document.getElementById('colleagueEmail2').value;

        if (userEmail) localStorage.setItem('userEmail', userEmail);
        if (colleagueEmail1) localStorage.setItem('colleagueEmail1', colleagueEmail1);
        if (colleagueEmail2) localStorage.setItem('colleagueEmail2', colleagueEmail2);

        modal.style.display = 'none';
        registrarBien();
    });

    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
        registrarBien();
    });

    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
            registrarBien();
        }
    });
}
*/