// editor.js
import { speak } from './utils.js';
import { addToGallery } from './gallery.js';

let cropper = null;
let currentImage = null;
let isCropMode = false;

export function initializeImageEditor() {
    const modal = document.getElementById('editorModal');
    const editorContainer = document.querySelector('.editor-container');

    // Asegurarse de que solo exista un contenedor de botones
    const existingButtonContainer = editorContainer.querySelector('.editor-button-container');
    if (existingButtonContainer) {
        existingButtonContainer.remove();
    }

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'editor-button-container';

    const buttons = [
        { id: 'cropBtn', icon: 'fa-crop-alt', text: 'Recortar' },
        { id: 'zoomInBtn', icon: 'fa-search-plus', text: 'Zoom +' },
        { id: 'zoomOutBtn', icon: 'fa-search-minus', text: 'Zoom -' },
        { id: 'rotateLeftBtn', icon: 'fa-undo', text: 'Rotar' },
        { id: 'rotateRightBtn', icon: 'fa-redo', text: 'Rotar' },
        { id: 'saveBtn', icon: 'fa-save', text: 'Guardar' }
    ];

    buttons.forEach(button => {
        const btn = document.createElement('button');
        btn.id = button.id;
        btn.className = 'editor-btn';
        btn.innerHTML = `<i class="fas ${button.icon}"></i> ${button.text}`;
        buttonContainer.appendChild(btn);
    });

    if (editorContainer) {
        editorContainer.insertBefore(buttonContainer, editorContainer.firstChild);
    }

    // Event listeners
    document.getElementById('cropBtn')?.addEventListener('click', toggleCrop);
    document.getElementById('zoomInBtn')?.addEventListener('click', () => zoom(0.1));
    document.getElementById('zoomOutBtn')?.addEventListener('click', () => zoom(-0.1));
    document.getElementById('rotateLeftBtn')?.addEventListener('click', () => rotate(-90));
    document.getElementById('rotateRightBtn')?.addEventListener('click', () => rotate(90));
    document.getElementById('saveBtn')?.addEventListener('click', saveEdited);

    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeEditor);
    }

    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeEditor();
        }
    });
}

export function openImageEditor(imageData) {
    const modal = document.getElementById('editorModal');
    const imageElement = document.getElementById('image-to-edit');
    
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    
    currentImage = imageData;
    imageElement.src = imageData;
    modal.style.display = 'block';
    
    const cropBtn = document.getElementById('cropBtn');
    if (cropBtn) {
        cropBtn.textContent = '✂️ Recortar';
        cropBtn.classList.remove('active');
    }
    
    isCropMode = false;
    speak("Editor de imagen abierto");
}

function closeEditor() {
    const modal = document.getElementById('editorModal');
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    isCropMode = false;
    currentImage = null;
    modal.style.display = 'none';
    speak("Editor cerrado");
}

function toggleCrop() {
    const imageElement = document.getElementById('image-to-edit');
    const cropBtn = document.getElementById('cropBtn');
    
    if (!isCropMode) {
        if (cropper) {
            cropper.destroy();
        }
        
        cropper = new Cropper(imageElement, {
            viewMode: 1,
            dragMode: 'move',
            aspectRatio: NaN,
            autoCrop: true,
            movable: true,
            rotatable: true,
            scalable: true,
            zoomable: true,
            minCropBoxWidth: 50,
            minCropBoxHeight: 50,
            cropBoxResizable: true,
            cropBoxMovable: true,
            background: true,
            ready: function() {
                this.cropper.crop();
            }
        });
        
        isCropMode = true;
        if (cropBtn) {
            cropBtn.textContent = '✂️ Aplicar';
            cropBtn.classList.add('active');
        }
        speak("Modo recorte activado");
    } else {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        isCropMode = false;
        if (cropBtn) {
            cropBtn.textContent = '✂️ Recortar';
            cropBtn.classList.remove('active');
        }
        imageElement.src = currentImage;
        speak("Modo recorte desactivado");
    }
}

function zoom(factor) {
    if (cropper) {
        cropper.zoom(factor);
    }
}

function rotate(degrees) {
    if (cropper) {
        cropper.rotate(degrees);
    }
}

async function saveEdited() {
    try {
        let editedImageData;
        
        if (cropper && isCropMode) {
            const cropData = cropper.getData();
            console.log('Crop Data:', cropData);

            const canvas = cropper.getCroppedCanvas({
                width: Math.round(cropData.width),
                height: Math.round(cropData.height),
                minWidth: 50,
                minHeight: 50,
                maxWidth: 4096,
                maxHeight: 4096,
                fillColor: '#fff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high',
            });

            if (!canvas) {
                throw new Error('Error al crear el canvas para el recorte');
            }

            editedImageData = canvas.toDataURL('image/jpeg', 0.95);
        } else {
            editedImageData = currentImage;
        }

        if (!editedImageData) {
            throw new Error('No se pudo obtener la imagen editada');
        }

        await addToGallery(editedImageData, true);
        closeEditor();
        speak("Imagen editada guardada en galería");

    } catch (error) {
        console.error('Error al guardar la imagen editada:', error);
        speak("Error al guardar la imagen editada");
    }
}