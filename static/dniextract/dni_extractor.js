function cargarContenidoSegunAnchoPantalla() {
    var contenedor = document.getElementById("contenedor");
    var anchoPantalla = window.innerWidth;
    
    // Definir los puntos de quiebre para cargar las plantillas HTML
    var breakpoint1 = 600; // Por ejemplo, 600px de ancho
    var breakpoint2 = 1000; // Otro ejemplo, 1000px de ancho

    // Seleccionar la plantilla HTML y la hoja de estilo según el ancho de la pantalla
    var plantillaHTML, hojaEstilo;

    if (anchoPantalla < breakpoint1) {
        plantillaHTML = '../../templates/html/diseno1.html';
        hojaEstilo = '../../templates/css/estilo1.css';
    } else if (anchoPantalla < breakpoint2) {
        plantillaHTML = '../../templates/html/diseno2.html';
        hojaEstilo = '../../templates/css/estilo2.css';
    } else {
        plantillaHTML = '../../templates/html/diseno3.html';
        hojaEstilo = '../../templates/css/estilo3.css';
    }

    // Cargar la hoja de estilo correspondiente
    var linkEstilo = document.createElement("link");
    linkEstilo.rel = "stylesheet";
    linkEstilo.href = hojaEstilo;
    document.head.appendChild(linkEstilo);

    // Cargar la plantilla HTML
    fetch(plantillaHTML)
        .then(response => response.text())
        .then(html => {
            contenedor.innerHTML = html;
        });
}

window.onload = cargarContenidoSegunAnchoPantalla;
window.addEventListener('resize', cargarContenidoSegunAnchoPantalla);
