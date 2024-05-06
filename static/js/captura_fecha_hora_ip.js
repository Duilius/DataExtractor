// Función para asignar fecha y hora a los inputs ocultos
function asignarFechaHora() {
    // Obtener la fecha y la hora actuales
    var hoy = new Date();
    var fecha = hoy.toISOString().split('T')[0]; // Formato de fecha (YYYY-MM-DD)
    var hora = hoy.toTimeString().split(' ')[0]; // Formato de hora (HH:MM:SS)

    // Asignar valores a los campos ocultos del formulario
    document.getElementById('laFecha').value = fecha;
    document.getElementById('laHora').value = hora;
}

function toggleMenu(){
    
    var menu = document.getElementById('vertical-menu');
    if (menu.style.left === '-200px') {
        menu.style.left = '0';
    } else {
        menu.style.left = '-200px';
    }
}
