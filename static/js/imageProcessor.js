// imageProcessor.js
console.log('Cargando imageProcessor.js');

const MAX_WIDTH = 1024;
const MAX_HEIGHT = 1024;

export async function processImage(imageData) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = function() {
            let width = img.width;
            let height = img.height;
            let resized = false;

            if (width > MAX_WIDTH || height > MAX_HEIGHT) {
                const ratio = Math.min(MAX_WIDTH / width, MAX_HEIGHT / height);
                width = Math.floor(width * ratio);
                height = Math.floor(height * ratio);
                resized = true;
            }

            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            const processedImageData = canvas.toDataURL('image/jpeg', 0.85);
            resolve({ imageData: processedImageData, resized: resized });
        };
        img.onerror = reject;
        img.src = imageData;
    });
}

export function isImageWithinSizeLimits(imageData) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = function() {
            resolve(img.width <= MAX_WIDTH && img.height <= MAX_HEIGHT);
        };
        img.src = imageData;
    });
}