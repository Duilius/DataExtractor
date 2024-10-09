// inventario_activos2.js
document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const cameraToggle = document.getElementById('cameraToggle');
    const tomarFotoBtn = document.getElementById('tomarFoto');
    const voiceCaptureBtn = document.getElementById('voiceCaptureBtn');
    const miniaturas = document.getElementById('miniaturas');
    const eliminarFotoBtn = document.getElementById('eliminarFoto');
    const guardarFotoBtn = document.getElementById('guardarFoto');
    const procesarFotoBtn = document.getElementById('procesarFoto');
    const subirFotoBtn = document.getElementById('subirFoto');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const formSection = document.getElementById('form-section');

    let fotosNoGuardadas = false;

    loginBtn.addEventListener('click', () => {
        alert("Login functionality to be implemented");
    });

    logoutBtn.addEventListener('click', () => {
        if (fotosNoGuardadas && confirm("Hay fotos no guardadas, ¿deseas salir de todas formas?")) {
            alert("Logged out");
        } else if (!fotosNoGuardadas) {
            alert("Logged out");
        }
    });

    cameraToggle.addEventListener('click', toggleCamera);
    tomarFotoBtn.addEventListener('click', capturePhoto);
    voiceCaptureBtn.addEventListener('click', toggleVoiceCapture);

    miniaturas.addEventListener('change', (event) => {
        if (event.target.classList.contains('fotoCheckbox')) {
            activarBotones();
        }
    });

    eliminarFotoBtn.addEventListener('click', eliminarFotosSeleccionadas);
    guardarFotoBtn.addEventListener('click', mostrarOpcionesGuardado);
    procesarFotoBtn.addEventListener('click', mostrarFormularioProcesamiento);
    subirFotoBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', handleFileSelect);

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '#e9e9e9';
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '';
        handleFiles(e.dataTransfer.files);
    });

    function activarBotones() {
        const checkboxes = document.querySelectorAll('.fotoCheckbox:checked');
        const activar = checkboxes.length > 0;
        eliminarFotoBtn.disabled = !activar;
        guardarFotoBtn.disabled = !activar;
        procesarFotoBtn.disabled = !activar;
    }

    function eliminarFotosSeleccionadas() {
        const fotosSeleccionadas = document.querySelectorAll('.fotoCheckbox:checked');
        if (fotosSeleccionadas.length === 0) {
            alert("Por favor, seleccione al menos una foto para eliminar.");
            return;
        }
        
        if (confirm(`¿Está seguro de que desea eliminar ${fotosSeleccionadas.length} foto(s)?`)) {
            fotosSeleccionadas.forEach(checkbox => checkbox.parentElement.remove());
            activarBotones();
            speak(`${fotosSeleccionadas.length} foto${fotosSeleccionadas.length > 1 ? 's' : ''} eliminada${fotosSeleccionadas.length > 1 ? 's' : ''}`);
        }
    }

    function mostrarOpcionesGuardado() {
        const options = ["Guardar en Drive", "Guardar en Servidor", "Guardar en Local"];
        const selectedOption = prompt(`Seleccione una opción de guardado:\n1. ${options[0]}\n2. ${options[1]}\n3. ${options[2]}\n\nIngrese el número de la opción:`);

        switch(selectedOption) {
            case "1": guardarEnDrive(); break;
            case "2": guardarEnServidor(); break;
            case "3": guardarEnLocal(); break;
            default: alert("Opción no válida o cancelada.");
        }
    }

    function mostrarFormularioProcesamiento() {
        formSection.style.display = 'block';
        setTimeout(() => formSection.classList.add('visible'), 10);
        procesarImagenes();
    }

    function handleFileSelect(e) {
        handleFiles(e.target.files);
    }

    function handleFiles(files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => addPhotoToGallery(e.target.result);
                reader.readAsDataURL(file);
            }
        });
    }

    // Estas funciones deben ser implementadas según tus necesidades específicas
    function guardarEnDrive() {
        alert("Función guardarEnDrive no implementada");
    }

    function guardarEnServidor() {
        alert("Función guardarEnServidor no implementada");
    }

    function guardarEnLocal() {
        alert("Función guardarEnLocal no implementada");
    }

    window.activarBotones = activarBotones; // Hacer la función global para que sea accesible desde camera_functions.js
});