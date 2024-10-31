// Asegúrate de que este código esté en un archivo JavaScript cargado después de que el DOM esté listo

document.addEventListener('DOMContentLoaded', function() {
    const registerBtn = document.getElementById('registrarFoto');
    const discardBtn = document.getElementById('descartarData');

    registerBtn.addEventListener('click', registerAndSendEmail);
    discardBtn.addEventListener('click', discardData);

    function registerAndSendEmail() {
        const formData = new FormData(document.getElementById('item-form'));
        
        // Añadir los emails al formData
        const userEmail = localStorage.getItem('userEmail') || '';
        const colleagueEmail1 = localStorage.getItem('colleagueEmail1') || '';
        const colleagueEmail2 = localStorage.getItem('colleagueEmail2') || '';
        
        formData.append('userEmail', userEmail);
        formData.append('colleagueEmail1', colleagueEmail1);
        formData.append('colleagueEmail2', colleagueEmail2);

        // Añadir los valores de los radio buttons
        const enUso = document.querySelector('input[name="enUso"]:checked');
        const estado = document.querySelector('input[name="estado"]:checked');
        formData.append('enUso', enUso ? enUso.value : '');
        formData.append('estado', estado ? estado.value : '');

        // Añadir las imágenes
        const imageGallery = document.getElementById('miniaturas');
        const images = imageGallery.getElementsByTagName('img');
        for (let i = 0; i < images.length; i++) {
            formData.append('images', images[i].src);
        }

        // Enviar los datos al servidor
        fetch('/api/register', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Registro exitoso. Se han enviado los correos de confirmación.');
                // Aquí puedes añadir lógica adicional post-registro, como limpiar el formulario
            } else {
                throw new Error(data.message || 'Error en el registro');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Hubo un error en el proceso de registro: ' + error.message);
        });
    }

    function discardData() {
        if (confirm('¿Está seguro de que desea descartar los datos?')) {
            document.getElementById('item-form').reset();
            // Aquí puedes añadir lógica adicional para limpiar otros elementos si es necesario
        }
    }
});