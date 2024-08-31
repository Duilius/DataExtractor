function abreModal(){
// Obtener elementos del DOM
const modal = document.getElementById("loginModal");
const btn = document.getElementById("loginBtn");
const span = document.getElementsByClassName("close")[0];

// Abrir el modal al hacer clic en el botón
btn.onclick = function() {
    
    modal.style.display = "block";
}

// Cerrar el modal al hacer clic en el <span> (x)
span.onclick = function() {
    modal.style.display = "none";
}

// Cerrar el modal al hacer clic fuera del contenido del modal
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Opcional: manejar eventos de los enlaces "Se me olvidó la contraseña" y "Cambiar de contraseña"
document.getElementById("forgotPassword").onclick = function(event) {
    event.preventDefault();
    alert("Recuperación de contraseña no implementada.");
}

document.getElementById("changePassword").onclick = function(event) {
    event.preventDefault();
    alert("Cambio de contraseña no implementado.");
}
}

function verificaUserCorreo(){

//VERIFICAR USERNAME Y PASSWORD EN VENTANA MODAL
//document.addEventListener("DOMContentLoaded", function() {
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const usernameMessage = document.getElementById("usernameMessage");
    const passwordMessage = document.getElementById("passwordMessage");

    //usernameInput.addEventListener("blur", function() {
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(usernameInput.value)) {
            usernameMessage.textContent = "El formato del correo electrónico no es válido.";
            usernameMessage.style.color = "red";
        } else {
            usernameMessage.textContent = "";
            // Verificar si el email existe en el servidor
            fetch(`/verify-username?username=${usernameInput.value}`)
                .then(response => response.json())
                .then(data => {
                    if (data.existe=="False") {
                        usernameMessage.textContent = "El usuario no existe.";
                        usernameMessage.style.color = "red";
                    } else {
                        //alert("usuario ==>" + data.name);
                        //usernameMessage.innerHTML = "User exists. ID: ${data.id}, Name: ${data.name}";
                        usernameMessage.innerHTML = " <i class='bx bx-check-circle' style='color:#11df49; font-size:1.25em;'></i> Bienvenido"
                        usernameMessage.style.color = "black";
                    }
                });
        }
    //});
}

//ONFOCUS: Se activa cuando cursor está dentro del input
function avisaFormatoClave(){
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const usernameMessage = document.getElementById("usernameMessage");
    const passwordMessage = document.getElementById("passwordMessage");

    if (passwordInput.value=="") {
        passwordMessage.textContent = "La contraseña es su WhatsApp [sin código de país].";
        passwordMessage.style.color = "green";
    }
}


//ONKEYUP: Se activa cuando se presiona una tecla que no es número
function soloDigitos(){
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const usernameMessage = document.getElementById("usernameMessage");
    const passwordMessage = document.getElementById("passwordMessage");
    const botonRegistro = document.getElementById("boton_registro");
    // Verifica si el campo de contraseña no está vacío y contiene solo números
    if (passwordInput.value.trim() === "" || /^\d+$/.test(passwordInput.value)) {
        // Si el campo está vacío o solo contiene números, habilita el botón de registro
        botonRegistro.disabled = false;
        passwordMessage.innerHTML = "";
        botonRegistro.style.background = ""; // Restaura el color de fondo del botón
    } else {
        // Si el campo contiene caracteres que no son números, deshabilita el botón de registro
        botonRegistro.disabled = true;
        passwordMessage.innerHTML = "<i class='bx bx-error' style='color:#e50909; font-size:1.15em;'></i> Solo digite números.";
        passwordMessage.style.color = "red";
        botonRegistro.style.background = "red";
    }
}


//ONBLUR: Cuando el usuario llega y se va del input
function verificaPassword(){
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const usernameMessage = document.getElementById("usernameMessage");
    const passwordMessage = document.getElementById("passwordMessage");

    //passwordInput.addEventListener("blur", function() {
        
        if (!passwordInput.value) {
            passwordMessage.textContent = "La contraseña es: Su WhatsApp [sin código de país].";
            passwordMessage.style.color = "red";
        } else {
                passwordMessage.textContent = "";
        }
        
    //});
//});
}

//CARGA FOTO DE EMPLEADO RESPONSABLE DEL BIEN INVENTARIADO
function fotoChica(input) {
    alert("ssssssssssssss");
            const foto_chica = document.getElementById("foto-empleado");

            if (input.value === "") {
                foto_chica.src = "{{ url_for('static', path='img/foto-no-hallado.jpeg') }}";
            } else {
                foto_chica.src = "{{ url_for('static', path='dniextract/img/') }}" + input.value + ".jpeg";
            }
}