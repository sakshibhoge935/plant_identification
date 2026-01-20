let videoStream = null;

function switchTab(mode) {
    // Hide all sections
    document.querySelectorAll('.mode-section').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tabs button').forEach(el => el.classList.remove('active'));

    // Show selected
    document.getElementById('section-' + mode).classList.remove('hidden');
    document.getElementById('tab-' + mode).classList.add('active');

    if (mode === 'webcam') startWebcam();
    else stopWebcam();
}

function startWebcam() {
    const video = document.getElementById('video');
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                videoStream = stream;
                video.srcObject = stream;
            })
            .catch(err => console.error("Camera Error:", err));
    }
}

function stopWebcam() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

function captureWebcam() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    
    // Draw video frame to canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    // Convert to Base64
    const dataURL = canvas.toDataURL('image/jpeg');
    sendData(dataURL, 'webcam');
}

function uploadImage() {
    const fileInput = document.getElementById('file-input');
    if (fileInput.files.length === 0) return alert("Please select a file!");
    
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    
    postData(formData);
}

function sendData(base64Data, type) {
    const formData = new FormData();
    formData.append("webcam_image", base64Data);
    postData(formData);
}

function postData(formData) {
    // Show loading state
    document.getElementById('result-container').classList.remove('hidden');
    document.getElementById('res-name').innerText = "Identifying...";
    
    fetch('/identify', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if(data.error) {
            alert(data.error);
        } else {
            document.getElementById('result-img').src = data.image_url;
            document.getElementById('res-name').innerText = data.plant_name;
            document.getElementById('res-prob').innerText = data.probability;
        }
    })
    .catch(error => console.error('Error:', error));
}
