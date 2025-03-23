const dropArea = document.getElementById('drop-area');
const resultTitle = document.getElementById('result-title');
const resultDiv = document.getElementById('result');
const apiButton = document.getElementById('api-button');
const apiModal = document.getElementById('api-modal');
const closeModal = document.getElementsByClassName('close')[0];

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
});

dropArea.addEventListener('drop', handleDrop, false);

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    const file = files[0];
    if (file && file.type === 'application/pdf') {
        uploadFile(file);
    } else {
        alert('Please upload a PDF file.');
    }
}

// Modal functionality
apiButton.onclick = function() {
    apiModal.style.display = 'block';
}

closeModal.onclick = function() {
    apiModal.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target == apiModal) {
        apiModal.style.display = 'none';
    }
}

// Display curl command
document.addEventListener('DOMContentLoaded', (event) => {
    const port = window.location.port ? `:${window.location.port}` : '';
    const url = `${window.location.protocol}//${window.location.hostname}${port}/upload`;
    const curlCommand = `curl -X POST -F file=@path/to/your/file.pdf ${url}`;
    document.getElementById('curl-command').textContent = curlCommand;
});

// // Copy result to clipboard
// document.getElementById('copy-button').addEventListener('click', () => {
//     const resultText = document.getElementById('result').textContent;
//     navigator.clipboard.writeText(resultText).then(() => {
//         alert('Text copied to clipboard');
//     }).catch(err => {
//         console.error('Failed to copy text: ', err);
//     });
// });

// API call to upload file
async function uploadFile(file) {
    let formData = new FormData();
    formData.append("file", file);

    // Clear previous result
    resultTitle.style.display = 'none';
    resultDiv.style.display = 'none';
    resultDiv.textContent = '';

    // Show loading spinner
    const spinner = document.getElementById('loading-spinner');
    spinner.style.display = 'block';

    try {
        const response = await fetch("http://localhost:5000/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (data.status === 'success') {
            resultTitle.style.display = 'block';
            resultDiv.style.display = 'block';
            resultDiv.textContent = data.body;
        } else {
            resultDiv.textContent = `Error: ${data.error}`;
        }
    } catch (error) {
        resultDiv.textContent = `Error: ${error.message}`;
    } finally {
        // Hide loading spinner
        spinner.style.display = 'none';
    }
}