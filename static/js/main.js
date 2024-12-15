// main.js

// Campos obligatorios definidos en el alcance global
const camposObligatorios = [
    { id: 'worker', tipo: 'input' },
    { id: 'cod-2024', tipo: 'input' },
    { id: 'color', tipo: 'input' },
    { id: 'descripcion', tipo: 'input' },
    { id: 'estado', tipo: 'select' }
];

import { speak } from './utils.js';
import { limpiarFormulario } from './formHandler.js';
import { mostrarMensajeModal } from './utils.js';
import { procesarImagenes } from './camera_functions.js';
import { initializeCamera } from './camera.js';
import { initializeGallery } from './gallery.js';
import { initializeImageEditor } from './imageEditor.js';
import { initializeFormHandler } from './formHandler.js';
import { initializeUtils, initializeAuthModal, checkAuthBeforeProcessing, showAuthModal } from './utils.js';
import { initializeSearch } from './search.js';
import { initializeWorkerInfo } from './worker_info.js';
import './imageProcessor.js';

// Contador de registros exitosos
let registrosExitosos = parseInt(localStorage.getItem('registrosExitosos') || '0');

window.addEventListener('DOMContentLoaded', (event) => {
    console.log('DOM completamente cargado en main.js');
    
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

    // Cargar el contenido del modal de autenticación
/*
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
*/

    // Event listeners para campos obligatorios
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
});

// Función global para cerrar el modal principal
window.closeModal = function() {
    document.getElementById('modal').style.display = "none";
}

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


function mostrarModalMedidasFaltantes(medidasFaltantes) {
    // Crear el modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay-faltantes';

    modal.innerHTML = `
        <div class="modal-faltantes" style='color:#000;'>
            <h3>Medidas Faltantes</h3>
            <p>Faltan las siguientes medidas: ${medidasFaltantes.join(', ')}.</p>
            <p>¿Desea subsanar las medidas o continuar sin registrarlas?</p>
            <div class="modal-actions-faltantes">
                <button id="subsanar-medidas" class="btn-faltantes btn-primary-faltantes">Subsanar</button>
                <button id="continuar-sin-medidas" class="btn-faltantes btn-secondary-faltantes">Enviar de todas formas</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Manejar el botón Subsanar
    document.getElementById('subsanar-medidas').addEventListener('click', () => {
        modal.remove();
    });

    // Manejar el botón Enviar de todas formas
    document.getElementById('continuar-sin-medidas').addEventListener('click', () => {
        modal.remove();
        document.querySelector('#formulario-bienes').submit();
    });
}




// Validar formulario
function validarFormulario() {
    console.log("Iniciando validación");
    let valido = true;
    let errores = [];

    // Validación de campos obligatorios
    camposObligatorios.forEach(campo => {
        const elemento = document.querySelector(`#${campo.id}`);
        if (!elemento) {
            valido = false;
            errores.push(`Campo ${campo.id} no encontrado`);
            return;
        }

        let valor = campo.tipo === 'input' || campo.tipo === 'select' ? 
                    elemento.value : 
                    elemento.textContent;

        if (!valor || valor.trim() === '' || valor === 'No disponible') {
            valido = false;
            elemento.classList.add('error');
            alert("Campo es: " + campo.id);    
            if (campo.id === 'worker'){
                errores.push(`Campo Trabajador es obligatorio`);    
            } else{

                errores.push(`Campo ${campo.id} es obligatorio`);
            }

        } else {
            elemento.classList.remove('error');
        }
    });

    // Validación del campo nuevo_usuario
    //const nuevoUsuarioInput = document.querySelector('#nuevo_usuario');
    //if (nuevoUsuarioInput) {
    //    const nuevoUsuario = nuevoUsuarioInput.value.trim();
    //    if (nuevoUsuario.length > 0 && nuevoUsuario.length < 8) {
    //        valido = false;
    //        nuevoUsuarioInput.classList.add('error');
    //        errores.push('El campo "Nuevo usuario" debe tener 8 caracteres');
   //     } else {
    //        nuevoUsuarioInput.classList.remove('error');
    //    }
   // }

    // Validación condicional de dimensiones
    const descripcion = document.querySelector('#descripcion').value.toLowerCase();
    const muebles = ['escritorio', 'mueble', 'mesa', 'repostero', 'estante', 
                     'archivador', 'credenza', 'pizarra', 'armario', 'librero', 
                     'persiana', 'cortina'];

    if (muebles.some(mueble => descripcion.includes(mueble))) {
        const medidas = ['largo', 'alto', 'ancho'];

        medidas.forEach(medida => {
            const inputMedida = document.querySelector(`#${medida}`);
            if (inputMedida && (!inputMedida.value || isNaN(inputMedida.value))) {
                inputMedida.value = '0'; // Asignar 0 si está vacío o es inválido
                inputMedida.classList.add('highlight');
            } else if (inputMedida) {
                inputMedida.classList.remove('highlight');
            }
        });
    }

    if (!valido) {
        mostrarMensajeModal(errores[0], true);
        return false;
    }

    return true;
}


// Función para limpiar la galería
function limpiarGaleria() {
    console.log("Limpiando galería...");
    const galeria = document.querySelector('#miniaturas'); // Asegúrate de que este ID sea correcto
    if (galeria) {
        galeria.innerHTML = ''; // Vaciar contenido de la galería
    }
}


// Función para registrar el bien
// Modificación en la lógica de registro exitoso
async function registrarBien() {
    console.log("Iniciando proceso de registro");

    if (!validarFormulario()) {
        return;
    }

    try {
        const formData = new FormData();
        const campos = {
            /*'codigoOficina': '#codigoOficina',*/
            'worker': '#worker', /* Código de Custodio */ 
            /*'situacion_prov': '#situacion-prov',*/
            'area_actual_id':'#hiddenAreaId',
            'describe_area':'#describe_area',
            'nuevo_usuario':'#nuevo_usuario',
            'acciones':'#acciones',
            'cod_patr': '#cod-patr',
            'cod_2024': '#cod-2024',
            'cod_2023': '#cod-2023',
            'cod_2022': '#cod-2022',
            'cod_2021': '#cod-2021',
            'cod_2020': '#cod-2020',
            'color': '#color',
            'material': '#material',
            'largo': '#largo',
            'ancho': '#ancho',
            'alto': '#alto',
            'marca': '#marca',
            'modelo': '#modelo',
            'num_serie': '#num-serie',
            'num_placa': '#num-placa',
            'num_chasis': '#num-chasis',
            'num_motor': '#num-motor',
            'anio_fabricac': '#anio-fabricac',
            'descripcion': '#descripcion',
            'observaciones': '#observaciones'
        };

        for (const [key, selector] of Object.entries(campos)) {
            const elemento = document.querySelector(selector);
            let valor = elemento ? elemento.value : '';
            if (['largo', 'ancho', 'alto'].includes(key)) {
                valor = valor && !isNaN(valor) ? valor : '0';
            }
            formData.append(key, valor);
        }

         // Mostrar alertas con los valores de los campos seleccionados
         const hiddenAreaId = document.querySelector('#hiddenAreaId')?.value || 'No definido';
         const describeArea = document.querySelector('#describe_area')?.value || 'No definido';
         const acciones = document.querySelector('#acciones')?.value || 'No definido';
         const color = document.querySelector('#color')?.value || 'No definido';
 

        const enUso = document.querySelector('input[name="enUso"]:checked')?.value || 'No';
        formData.append('enUso', enUso);

        const estado = document.querySelector('#estado')?.value || '';
        formData.append('estado', estado);

        const response = await fetch('/registrar_bien', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok && data.exito) {
            mostrarMensajeModal('Registro completado con éxito', false);

            // Limpiar formulario y galería
            limpiarFormulario();
            document.querySelector("#form-section").style.display = 'none'; // Lo oculta
            limpiarGaleria();

        } else {
            mostrarMensajeModal(data.error || 'Error en el registro', true);
        }

    } catch (error) {
        console.error('Error:', error);
        mostrarMensajeModal('Error al procesar el registro: ' + error.message, true);
    }
}


// Event listeners principales
document.addEventListener('DOMContentLoaded', function() {
    // Botones principales
    const registrarBtn = document.getElementById('registrarFoto');
    const descartarBtn = document.getElementById('descartarData');
    const procesarBtn = document.getElementById('procesarFoto');

    if (registrarBtn) {
        registrarBtn.addEventListener('click', function() {
            console.log("Botón registrar clickeado");
            registrarBien();
        });
    }

    if (descartarBtn) {
        descartarBtn.addEventListener('click', function() {
            limpiarFormulario();
            const formSection = document.getElementById('form-section');
            if (formSection) {
                formSection.style.display = 'block';
            }
            mostrarMensajeModal('Formulario descartado', false);
        });
    }

    if (procesarBtn) {
        procesarBtn.addEventListener('click', () => {
            if (checkAuthBeforeProcessing()) {
                procesarImagenes();
            }
        });
    }
});

function solicitarEnvioReporte() {
    if (confirm('¿Desea recibir un reporte de los bienes registrados?')) {
        fetch('/enviar_reporte', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.enviado) {
                    mostrarMensajeModal('El reporte ha sido enviado a su correo', false);
                } else {
                    mostrarMensajeModal('Hubo un error al enviar el reporte', true);
                }
            })
            .catch(error => console.error('Error:', error));
    }
}


//Asigna valor 0 (CERO) a inputs #largo, #ancho y #alto
document.querySelectorAll('.medidas').forEach(input => {
    input.addEventListener('blur', () => {
        if (input.value === '') {
            input.value = '0';
        }
    });
});


// Hacer funciones globales disponibles
window.registrarBien = registrarBien;
window.validarFormulario = validarFormulario;
window.mostrarBarraProgreso = mostrarBarraProgreso;
//window.solicitarEnvioReporte = solicitarEnvioReporte;