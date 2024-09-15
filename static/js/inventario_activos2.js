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
            { codigo: '3619', nombre: 'Juan Pérez', cargo: 'Sub Gerencia de Operaciones', foto: 'jefe1.jpg' },
            { codigo: '1511', nombre: 'María García', cargo: 'Gerencia de Recursos Humanos', foto: 'jefe2.jpg' }
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

    // Agregar evento click a cada resultado
    document.querySelectorAll('.resultado').forEach(elem => {
        elem.addEventListener('click', seleccionarJefe);
    });
}

function seleccionarJefe(e) {
    const codigo = e.target.dataset.codigo;
    // Simular obtención de datos del jefe y su superior
    const jefe = { codigo: '3619', nombre: 'Juan Pérez', cargo: 'Sub Gerencia de Operaciones', foto: 'jefe1.jpg' };
    const superior = { codigo: '1511', nombre: 'María García', cargo: 'Gerencia de Recursos Humanos', foto: 'jefe2.jpg' };

    document.getElementById('jefeCodigo').textContent = jefe.codigo;
    document.getElementById('jefeNombre').textContent = jefe.nombre;
    document.getElementById('jefeArea').textContent = jefe.cargo;
    document.getElementById('jefeFoto').src = jefe.foto;

    document.getElementById('superiorCodigo').textContent = superior.codigo;
    document.getElementById('superiorNombre').textContent = superior.nombre;
    document.getElementById('superiorArea').textContent = superior.cargo;
    document.getElementById('superiorFoto').src = superior.foto;

    // Mostrar colaboradores (simulado)
    mostrarColaboradores();
}

function mostrarColaboradores() {
    const colaboradores = [
        { codigo: '2510', nombre: 'Pedro Gómez', cargo: 'Analista', foto: 'colab1.jpg' },
        { codigo: '2511', nombre: 'Ana Rodríguez', cargo: 'Asistente', foto: 'colab2.jpg' }
    ];

    const listaColaboradores = document.getElementById('listaColaboradores');
    listaColaboradores.innerHTML = colaboradores.map(c => 
        `<div class="colaborador">
            <p>Código: ${c.codigo}</p>
            <p>Apellidos y Nombres: ${c.nombre}</p>
            <p>Cargo: ${c.cargo}</p>
            <img src="${c.foto}" alt="Foto de ${c.nombre}" class="foto-colaborador">
        </div>`
    ).join('');
}

// Funcionalidad de la cámara (simulada)
const toggleCamara = document.getElementById('tomarFoto');
const visorCamara = document.getElementById('visorCamara');
const miniaturas = document.getElementById('miniaturas');

toggleCamara.addEventListener('click', () => {
    // Simular toma de foto
    const imgUrl = 'foto_simulada.jpg';
    
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
    if (e.target.classList.contains('miniatura') || e.target.classList.contains('foto-colaborador')) {
        modal.style.display = 'block';
        modalImg.src = e.target.src;
    }
});

span.onclick = () => modal.style.display = 'none';

// Funcionalidad de registro de bien
const registrarBtn = document.getElementById('registrar');
registrarBtn.addEventListener('click', () => {
    // Aquí iría la lógica para registrar el bien en la base de datos
    alert('Bien registrado exitosamente');
});

const descartarBtn = document.getElementById('descartar');
descartarBtn.addEventListener('click', () => {
    // Limpiar todos los campos del formulario
    document.querySelectorAll('#registroBien input, #registroBien textarea').forEach(elem => {
        elem.value = '';
    });
    document.querySelectorAll('#registroBien input[type="radio"]').forEach(elem => {
        elem.checked = false;
    });
});