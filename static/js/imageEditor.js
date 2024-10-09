// imageEditor.js
console.log('Cargando imageEditor.js');

import { processImage, isImageWithinSizeLimits } from './imageProcessor.js';

let cropper;
let selectedCrops = [];
let collageImage = null;

export function initializeImageEditor() {
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('miniatura')) {
            showLargeImage(event.target.src);
        }
    });
}


export function showLargeImage(src) {
    const overlay = document.createElement('div');
    overlay.className = 'image-overlay';
    
    const imageContainer = document.createElement('div');
    imageContainer.className = 'image-container';
    
    const largeImg = document.createElement('img');
    largeImg.src = src;
    largeImg.className = 'large-image';
    
    const editorContainer = createEditorButtons(src);
    
    imageContainer.appendChild(largeImg);
    overlay.appendChild(imageContainer);
    overlay.appendChild(editorContainer);
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'X';
    closeBtn.className = 'close-btn';
    closeBtn.onclick = closeLargeImage;
    overlay.appendChild(closeBtn);
    
    document.body.appendChild(overlay);
    
    initCrop(largeImg);
}


function addCurrentCropToCollage() {
    if (cropper) {
        const canvas = cropper.getCroppedCanvas({
            maxWidth: 1024,  // Limitamos cada recorte a 1024x1024 para mantener el collage dentro de 1024x1024
            maxHeight: 1024,
        });
        selectedCrops.push(canvas);
        alert('Recorte añadido al collage');
    }
}

function createCollage() {
    if (selectedCrops.length === 0) {
        alert('Por favor, añada al menos un recorte al collage');
        return;
    }

    const collageCanvas = document.createElement('canvas');
    const ctx = collageCanvas.getContext('2d');

    const numCrops = selectedCrops.length;
    const cols = Math.ceil(Math.sqrt(numCrops));
    const rows = Math.ceil(numCrops / cols);
    const cropSize = Math.floor(1024 / Math.max(cols, rows));

    collageCanvas.width = 1024;
    collageCanvas.height = 1024;

    // Rellenamos el canvas con un fondo blanco
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, collageCanvas.width, collageCanvas.height);

    selectedCrops.forEach((crop, index) => {
        const x = ((index % cols) * cropSize) + ((1024 - (cols * cropSize)) / 2);
        const y = (Math.floor(index / cols) * cropSize) + ((1024 - (rows * cropSize)) / 2);
        ctx.drawImage(crop, x, y, cropSize, cropSize);
    });

    collageImage = collageCanvas;
    
    // Mostrar el collage en la interfaz
    const largeImg = document.querySelector('.large-image');
    if (largeImg) {
        largeImg.src = collageCanvas.toDataURL('image/jpeg', 0.9);
    }

    alert('Collage creado con éxito. Presione "Guardar Cambios" para añadirlo a la galería.');
    selectedCrops = [];
}


export function closeLargeImage() {
    const overlay = document.querySelector('.image-overlay');
    if (overlay) {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        document.body.removeChild(overlay);
    }
}

function initCrop(img) {
    if (cropper) {
        cropper.destroy();
    }
    cropper = new Cropper(img, {
        aspectRatio: NaN,
        viewMode: 1,
        minCropBoxWidth: 50,  // Reducido de 200 a 50
        minCropBoxHeight: 50, // Reducido de 200 a 50
        ready: function() {
            this.cropper.crop();
        }
    });
}

function rotateImage(degree) {
    if (cropper) {
        cropper.rotate(degree);
    }
}

function zoomImage(ratio) {
    if (cropper) {
        cropper.zoom(ratio);
    }
}

async function saveEditedImage(originalSrc) {
    let imageToSave;
    
    if (collageImage) {
        imageToSave = collageImage.toDataURL('image/jpeg', 0.9);
        collageImage = null; // Resetear después de usar
    } else if (cropper) {
        const canvas = cropper.getCroppedCanvas({
            maxWidth: 1024,
            maxHeight: 1024,
        });
        imageToSave = canvas.toDataURL('image/jpeg', 0.9);
    } else {
        alert("No hay imagen para guardar");
        return;
    }

    try {
        const { imageData: processedImageData, resized } = await processImage(imageToSave);

        const event = new CustomEvent('addToGallery', { 
            detail: { imageData: processedImageData, isEdited: true } 
        });
        document.dispatchEvent(event);
        
        /*
        if (resized) {
            alert("La imagen ha sido redimensionada para cumplir con el tamaño máximo permitido de 1024x1024 píxeles.");
        } else {
            alert("La imagen ha sido guardada con éxito.");
        }
        */
        alert("La imagen ha sido guardada con éxito.");

        closeLargeImage();
        
        // Redirigir a la galería
        const galeriaSection = document.getElementById('galeria-section');
        if (galeriaSection) {
            galeriaSection.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        console.error("Error al procesar la imagen editada:", error);
        alert("Error al guardar la imagen editada");
    }
}


function createEditorButtons(src) {
    const buttonRows = [
        [
            { icon: 'fa-cut', text: 'Recortar', onClick: () => initCrop(document.querySelector('.large-image')) },
            { icon: 'fa-plus', text: 'Al Collage', onClick: addCurrentCropToCollage },
            { icon: 'fa-images', text: 'Crear Collage', onClick: createCollage },
            { icon: 'fa-save', text: 'Guardar', onClick: () => saveEditedImage(src) }
        ],
        [
            { icon: 'fa-undo', onClick: () => rotateImage(-90) },
            { icon: 'fa-redo', onClick: () => rotateImage(90) },
            { icon: 'fa-search-plus', onClick: () => zoomImage(0.1) },
            { icon: 'fa-search-minus', onClick: () => zoomImage(-0.1) }
        ]
    ];

    const editorContainer = document.createElement('div');
    editorContainer.className = 'editor-container';

    buttonRows.forEach((row, rowIndex) => {
        const rowDiv = document.createElement('div');
        rowDiv.className = `button-row ${rowIndex === 1 ? 'icon-only' : ''}`;
        
        row.forEach(button => {
            const btn = document.createElement('button');
            btn.className = 'edit-btn';
            btn.innerHTML = `<i class="fas ${button.icon}"></i>${button.text ? `<span class="btn-text">${button.text}</span>` : ''}`;
            btn.onclick = button.onClick;
            rowDiv.appendChild(btn);
        });

        editorContainer.appendChild(rowDiv);
    });

    return editorContainer;
}

export { 
    initCrop, 
    rotateImage, 
    zoomImage, 
    saveEditedImage 
};