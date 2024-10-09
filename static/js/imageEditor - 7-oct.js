// imageEditor.js
console.log('Cargando imageEditor.js');

let cropper;

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
    
    const editorContainer = document.createElement('div');
    editorContainer.className = 'editor-container';
    
    const cropButton = document.createElement('button');
    cropButton.textContent = 'Recortar';
    cropButton.onclick = () => initCrop(largeImg);
    
    const rotateLeftButton = document.createElement('button');
    rotateLeftButton.textContent = 'Rotar Izquierda';
    rotateLeftButton.onclick = () => rotateImage(-90);
    
    const rotateRightButton = document.createElement('button');
    rotateRightButton.textContent = 'Rotar Derecha';
    rotateRightButton.onclick = () => rotateImage(90);
    
    const zoomInButton = document.createElement('button');
    zoomInButton.textContent = 'Zoom In';
    zoomInButton.onclick = () => zoomImage(0.1);
    
    const zoomOutButton = document.createElement('button');
    zoomOutButton.textContent = 'Zoom Out';
    zoomOutButton.onclick = () => zoomImage(-0.1);
    
    const saveButton = document.createElement('button');
    saveButton.textContent = 'Guardar Cambios';
    saveButton.onclick = () => saveEditedImage(src);
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'X';
    closeBtn.className = 'close-btn';
    closeBtn.onclick = closeLargeImage;  // Cambiado para usar la función exportada
    
    editorContainer.appendChild(cropButton);
    editorContainer.appendChild(rotateLeftButton);
    editorContainer.appendChild(rotateRightButton);
    editorContainer.appendChild(zoomInButton);
    editorContainer.appendChild(zoomOutButton);
    editorContainer.appendChild(saveButton);
    
    imageContainer.appendChild(largeImg);
    overlay.appendChild(imageContainer);
    overlay.appendChild(editorContainer);
    overlay.appendChild(closeBtn);
    document.body.appendChild(overlay);
    
    initCrop(largeImg);
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
        minCropBoxWidth: 200,
        minCropBoxHeight: 200,
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

function saveEditedImage(originalSrc) {
    if (cropper) {
        const canvas = cropper.getCroppedCanvas({
            width: 800,  // Limitar el ancho, ajusta el valor a lo que necesitas
            height: 600, // Limitar el alto, ajusta el valor a lo que necesitas
        });

        // Cambia a JPEG para reducir el tamaño y ajusta la calidad (0.7 por ejemplo)
        const editedImageData = canvas.toDataURL('image/jpeg', 0.7);

        const event = new CustomEvent('imageSaved', { 
            detail: { originalSrc, editedImageData } 
        });
        document.dispatchEvent(event);
        
        closeLargeImage();
    }
}


export { initCrop, rotateImage, zoomImage, saveEditedImage };