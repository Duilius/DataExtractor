// Funcionalidad de modo oscuro
const darkModeToggle = document.getElementById('darkModeToggle');
darkModeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
});

// Funcionalidad de búsqueda de jefe (simulada)
const busquedaJefe = document.getElementById('busquedaJefe');
const resultadosBusqueda = document.getElementById('resultadosBusqueda');

busquedaJefe.addEventListener('input', (e) => {
    if (e.target.value.length >= 3) {
        // Simular una búsqueda en la base de datos
        const resultados = [
            { codigo: '3619', nombre: 'Juan Pérez', cargo: 'Gerente de Operaciones' },
            { codigo: '1511', nombre: 'María García', cargo: 'Jefe de Recursos Humanos' }
        ];
        mostrarResultados(resultados);
    } else {
        resultadosBusqueda.innerHTML = '';
    }
});

function mostrarResultados(resultados) {
    resultadosBusqueda.innerHTML = resultados.map(r => 
        `<div class="resultado" data-codigo="${r.codigo}">
            ${r.nombre} - ${r.cargo}
        </div>`
    ).join('');
}

// Funcionalidad de la cámara (simulada)
const toggleCamara = document.getElementById('toggleCamara');
const visorCamara = document.getElementById('visorCamara');
const tomarFoto = document.getElementById('tomarFoto');
const miniaturas = document.getElementById('miniaturas');

toggleCamara.addEventListener('click', () => {
    visorCamara.innerHTML = '<video id="video" width="100%" height="100%" autoplay></video>';
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            document.getElementById('video').srcObject = stream;
        })
        .catch(error => {
            console.error('Error accessing camera:', error);
        });
});

tomarFoto.addEventListener('click', () => {
    const video = document.getElementById('video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imgUrl = canvas.toDataURL('image/jpeg');
    
    const img = document.createElement('img');
    img.src = imgUrl;
    img.classList.add('miniatura');
    miniaturas.appendChild(img);
});

// Funcionalidad del modal de foto
const modal = document.getElementById('modalFoto');
const modalImg = document.getElementById('imgAmpliada');
const span = document.getElementsByClassName('cerrar')[0];

document.body.addEventListener('click', (e) => {
    if (e.target.classList.contains('miniatura')) {
        modal.style.display = 'block';
        modalImg.src = e.target.src;
    }
});

span.onclick = () => modal.style.display = 'none';

// Aquí deberías agregar más funcionalidades como:
// - Procesamiento de fotos
// - Registro de bienes
// - Manejo de colaboradores
// - Login/Logout
// - Conexión con base de datos