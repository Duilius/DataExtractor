document.addEventListener("DOMContentLoaded", function() {
    function selectUser(userId, userName) {
        const codigoSeleccionado = document.getElementById(`codigo-${userId}`);
        const nombresSeleccionados = document.getElementById(`nombres-${userId}`);
        const gerenciaSeleccionada = document.getElementById(`gerencia-${userId}`);
        const fotoSeleccionada = document.getElementById(`foto-${userId}`);

        document.getElementById('codigo-seleccionado').value = codigoSeleccionado.value;
        document.getElementById('nombres-seleccionado').value = nombresSeleccionados.value;
        document.getElementById('gerencia-seleccionado').value = gerenciaSeleccionada.value;
        document.getElementById('foto-seleccionada').value = fotoSeleccionada.value;

        document.getElementById('worker').value = userId;

        // Ocultar todas las tarjetas
        const empleados = document.querySelectorAll('#lista-usuarios .empleado');
        empleados.forEach(emp => emp.classList.add('oculto'));

        // Mostrar solo la tarjeta seleccionada
        document.getElementById(`empleado-${userId}`).classList.remove('oculto');

        // Mostrar botones ACEPTAR y DESCARTAR
        document.getElementById('aceptar-descartar').classList.remove('oculto');

        alert(`Tarjeta seleccionada: ${userName}`);
    }

    window.selectUser = selectUser; // Hacemos la función accesible globalmente

    function transferData() {
        alert('Transferir datos');
        // Aquí puedes agregar la lógica para transferir los datos a donde los necesites
    }

    window.transferData = transferData; // Hacemos la función accesible globalmente

    function resetSelection() {
        // Resetea la selección de usuario y oculta los botones
        document.getElementById('aceptar-descartar').classList.add('oculto');
        const empleados = document.querySelectorAll('#lista-usuarios .empleado');
        empleados.forEach(emp => emp.classList.remove('oculto'));
        alert('Selección descartada');
    }

    window.resetSelection = resetSelection; // Hacemos la función accesible globalmente
});
