// Función para enviar el ancho de la pantalla al servidor
    function enviarAnchoPantalla() {
        // Obtener el ancho de la pantalla
        var anchoPantalla = window.innerWidth;

        // Crear una solicitud XMLHttpRequest (o usa fetch si prefieres)
        var xhr = new XMLHttpRequest();
        
        // Configurar la solicitud con la URL y el método POST
        xhr.open("POST", "/cambiar_contenido", true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

        // Manejar la respuesta del servidor (opcional)
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4 && xhr.status == 200) {
                // Manejar la respuesta del servidor si es necesario
                console.log(xhr.responseText);
            }
        };

        // Convertir el objeto JavaScript a JSON y enviarlo
        var data = JSON.stringify({ ancho: anchoPantalla });
        xhr.send(data);
    }

    // Llamar a la función al cargar la página
    window.onload = enviarAnchoPantalla;

    // Llamar a la función cuando se redimensiona la pantalla
    window.addEventListener('resize', enviarAnchoPantalla);