// worker_info.js

export function initializeWorkerInfo() {
    const workerPhoto = document.getElementById('worker-photo');
    workerPhoto.addEventListener('click', enlargeWorkerPhoto);
}

function enlargeWorkerPhoto() {
    const photo = document.getElementById('worker-photo');
    const enlarged = photo.cloneNode();
    enlarged.removeAttribute('id');
    enlarged.classList.add('enlarged-photo');

    const overlay = document.createElement('div');
    overlay.classList.add('photo-overlay');
    overlay.appendChild(enlarged);

    overlay.addEventListener('click', () => {
        document.body.removeChild(overlay);
    });

    document.body.appendChild(overlay);
}

export function updateWorkerInfo(workerData) {
    const workerName = document.getElementById('worker-name');
    const workerArea = document.getElementById('worker-area');
    const workerPhoto = document.getElementById('worker-photo');

    workerName.textContent = workerData.name;
    workerArea.textContent = workerData.area;
    workerPhoto.src = workerData.photoUrl;
}