function showContact() {
    const contactForm = document.getElementById("contactForm");
    contactForm.style.display = contactForm.style.display === "none" ? "block" : "none";
}

let isAudioPlaying = false;
let audioInstance;

function playAudio() {
    const audioText = "La IA reemplaza hardware costoso como lectores RFID, reduciendo significativamente los costos operativos. Al utilizar únicamente dispositivos móviles para capturar datos de inventario, elimina la necesidad de infraestructura adicional y especializada. La captura de datos es instantánea, permitiendo a los usuarios registrar información de etiquetas en segundos. La IA procesa, organiza y actualiza la información en tiempo real, eliminando retrasos y acelerando la toma de decisiones.";
    audioInstance = new SpeechSynthesisUtterance(audioText);
    audioInstance.rate = 1.1;
    window.speechSynthesis.speak(audioInstance);
    isAudioPlaying = true;
    document.getElementById("audioControlButton").innerText = "Detener Audio";
}

function stopAudio() {
    window.speechSynthesis.cancel();
    isAudioPlaying = false;
    document.getElementById("audioControlButton").innerText = "Reproducir Audio";
}

function toggleAudio() {
    if (isAudioPlaying) {
        stopAudio();
    } else {
        playAudio();
    }
}

// Carrusel
let slideIndex = 0;
const slides = document.querySelectorAll(".carousel-slide");

function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.classList.remove("active");
        if (i === index) {
            slide.classList.add("active");
        }
    });
}

function nextSlide() {
    slideIndex = (slideIndex + 1) % slides.length;
    showSlide(slideIndex);
}

showSlide(slideIndex); // Mostrar el primer slide
setInterval(nextSlide, 3000); // Cambiar de slide cada 3 segundos
