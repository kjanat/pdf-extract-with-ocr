/**
 * PDF-Extract - Frontend JavaScript
 * Handles file uploads, result polling, and UI interactions
 */

// ===== Drag and Drop Handling =====
const dropArea = document.getElementById('drop-area');

// Set up drag and drop event listeners
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea?.addEventListener(eventName, preventDefaults, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    dropArea?.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea?.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
});

dropArea?.addEventListener('drop', handleDrop, false);

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    handleFiles(e.dataTransfer.files);
}

// ===== Document Ready Setup =====
document.addEventListener('DOMContentLoaded', () => {
    setupApiModal();
    setupCurlCommand();

    // Initialize job list if on jobs page
    if (document.getElementById('job-table-body')) {
        fetchJobs();
    }
});

function setupApiModal() {
    const apiButton = document.getElementById('api-button');
    const apiModal = document.getElementById('api-modal');
    const closeModal = document.querySelector('.modal .close');

    if (!apiButton || !apiModal) return;

    // Setup modal open/close
    apiButton.onclick = () => apiModal.style.display = 'block';
    closeModal.onclick = () => apiModal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === apiModal) {
            apiModal.style.display = 'none';
        }
    };
}

function setupCurlCommand() {
    const curlCommandElement = document.getElementById('curl-command');
    if (!curlCommandElement) return;

    const port = window.location.port ? `:${window.location.port}` : '';
    const url = `${window.location.protocol}//${window.location.hostname}${port}/upload`;
    curlCommandElement.textContent = `curl -X POST -F file=@path/to/your/file.pdf ${url}`;
}

// ===== File Upload Handling =====
function handleFiles(files) {
    if (!files || files.length === 0) return;

    // Clear previous results and show spinner
    const resultDiv = document.getElementById('result');
    if (resultDiv) resultDiv.innerHTML = '';

    showSpinner(true);

    // Handle single vs multiple files differently
    if (files.length === 1) {
        handleSingleFile(files[0]);
    } else {
        handleMultipleFiles(files);
    }
}

function handleSingleFile(file) {
    if (!isPdfFile(file)) {
        alert('Please upload a PDF file.');
        showSpinner(false);
        return;
    }

    uploadSingleFile(file);
}

function handleMultipleFiles(files) {
    let uploadCount = 0;

    for (const file of files) {
        if (isPdfFile(file)) {
            uploadMultipleFile(file);
            uploadCount++;
        } else {
            alert(`File "${file.name}" is not a PDF. Skipping.`);
        }
    }

    if (uploadCount > 0) {
        const resultDiv = document.getElementById('result');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="success-message">
                    Uploaded ${uploadCount} files for processing. 
                    Redirecting to jobs page...
                </div>
            `;
        }

        // Redirect to jobs page after a short delay
        setTimeout(() => {
            window.location.href = '/jobs';
        }, 2000);
    } else {
        showSpinner(false);
    }
}

function isPdfFile(file) {
    return file && file.type === 'application/pdf';
}

// ===== API Calls =====
function uploadSingleFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                pollForResults(data.task_id, file.name);
            } else {
                displayError(`Error uploading file: ${data.error || 'Unknown error'}`);
            }
        })
        .catch(error => {
            displayError(`Error uploading file: ${error.message}`);
        });
}

function uploadMultipleFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .catch(error => {
            console.error('Error uploading file:', error);
        });
}

function pollForResults(taskId, filename) {
    const resultDiv = document.getElementById('result');
    if (!resultDiv) return;

    const interval = setInterval(() => {
        fetch(`/status/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.state === 'COMPLETED') {
                    clearInterval(interval);
                    showSpinner(false);
                    fetchAndDisplayResult(taskId, resultDiv);
                } else if (data.state === 'FAILED') {
                    clearInterval(interval);
                    showSpinner(false);
                    displayError(`Processing failed: ${data.error_message || 'Unknown error'}`);
                }
                // Continue polling for PENDING state
            })
            .catch(error => {
                clearInterval(interval);
                showSpinner(false);
                displayError(`Error checking status: ${error.message}`);
            });
    }, 1000);
}

function fetchAndDisplayResult(taskId, resultDiv) {
    fetch(`/api/result/${taskId}`)
        .then(response => response.json())
        .then(data => {
            const extractedText = data.text || '';

            // Check if there's any meaningful text content
            if (extractedText.trim()) {
                // Display the extracted text with copy button
                resultDiv.innerHTML = `
                    <pre class="text-content">${extractedText}</pre>
                    <button id="copy-button" class="button">Copy Text</button>
                `;

                // Set up copy button functionality
                setupCopyButton('copy-button', '.text-content');

                // Make sure the result title is visible
                const resultTitle = document.getElementById('result-title');
                if (resultTitle) resultTitle.style.display = 'block';
            } else {
                // Hide both result and result title if no text was extracted
                resultDiv.innerHTML = `
                    <div class="info-message">No text could be extracted from this document.</div>
                `;

                // Hide the result title
                const resultTitle = document.getElementById('result-title');
                if (resultTitle) resultTitle.style.display = 'none';
            }
        })
        .catch(error => {
            displayError(`Error fetching results: ${error.message}`);
        });
}

// ===== Job Management =====
async function fetchJobs() {
    try {
        const response = await fetch('/api/jobs');
        const jobs = await response.json();

        const tbody = document.getElementById('job-table-body');
        if (!tbody) return;

        tbody.innerHTML = "";

        jobs.forEach(job => {
            const row = createJobTableRow(job);
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error fetching jobs:', error);
    }
}

function createJobTableRow(job) {
    const row = document.createElement('tr');

    // Add view button for completed jobs
    const viewResultBtn = job.status === 'COMPLETED'
        ? `<button class="small-button" onclick="viewResult('${job.id}')">View Text</button>`
        : '';

    // Format file size with 2 decimal places as MB
    // Assuming file_size_kb is in KB, convert to MB
    const fileSize = job.file_size_kb ? (job.file_size_kb / 1024).toFixed(2) : '-';

    row.innerHTML = `
        <td class="">${job.id}</td>
        <td>${job.filename}</td>
        <td class="status-${job.status}"><span>${job.status} ${viewResultBtn}</span></td>
        <td>${job.method || '-'}</td>
        <td>${job.page_count || '-'}</td>
        <td>${fileSize}</td>
        <td>${job.duration_ms || '-'}</td>
        <td>${new Date(job.created_at).toLocaleString()}</td>
    `;

    return row;
}

async function viewResult(taskId) {
    try {
        const response = await fetch(`/api/result/${taskId}`);
        const data = await response.json();
        const extractedText = data.text || '';
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        
        // Different content based on whether there's text to display
        if (extractedText.trim()) {
            modal.innerHTML = `
                <div class="modal-content">
                    <span class="close" onclick="this.parentElement.parentElement.remove()">×</span>
                    <h3>Extracted Text</h3>
                    <p><strong>File:</strong> ${data.filename}</p>
                    <div class="text-container">
                        <pre>${extractedText}</pre>
                    </div>
                    <button id="modal-copy-button" class="button">Copy Text</button>
                </div>
            `;
            
            document.body.appendChild(modal);
            setupCopyButton('modal-copy-button', '.text-container pre');
        } else {
            modal.innerHTML = `
                <div class="modal-content">
                    <span class="close" onclick="this.parentElement.parentElement.remove()">×</span>
                    <h3>No Text Found</h3>
                    <p><strong>File:</strong> ${data.filename}</p>
                    <div class="info-message">
                        No text could be extracted from this document.
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
        }
    } catch (error) {
        alert(`Error fetching result: ${error.message}`);
    }
}

// ===== Utility Functions =====
function showSpinner(show) {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

function displayError(message) {
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        resultDiv.innerHTML = `<div class="error-message">${message}</div>`;
    }
    showSpinner(false);
}

function setupCopyButton(buttonId, textSelector) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    button.addEventListener('click', () => {
        const textElement = document.querySelector(textSelector);
        if (!textElement) return;

        navigator.clipboard.writeText(textElement.textContent)
            .then(() => {
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = 'Copy Text';
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy text:', err);
            });
    });
}

function copyTableToClipboard() {
    const table = document.querySelector("table");
    if (!table) return;

    const range = document.createRange();
    range.selectNode(table);

    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    try {
        document.execCommand('copy');
        alert("Table copied to clipboard!");
    } catch (err) {
        alert("Failed to copy table.");
    }

    selection.removeAllRanges();
}

function downloadCSV() {
    const rows = [[
        "Task ID",
        "Filename",
        "Status",
        "Method",
        "Pages",
        "Size (MB)",
        "Duration (ms)",
        "Created"
    ]];

    document.querySelectorAll("#job-table-body tr").forEach(tr => {
        const row = Array.from(tr.querySelectorAll("td")).map(td => td.textContent.trim());
        rows.push(row);
    });

    const csvContent = rows.map(r => r.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "ocr_jobs.csv";
    link.click();
}

// For form-based uploads
async function uploadPDF() {
    const form = document.getElementById('upload-form');
    if (!form) return;

    const formData = new FormData(form);
    const uploadButton = document.getElementById('upload-button');
    const statusContainer = document.getElementById('status-container');

    if (uploadButton) uploadButton.disabled = true;
    if (statusContainer) statusContainer.innerHTML = '<p>Uploading file...</p>';

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.task_id) {
            if (statusContainer) {
                statusContainer.innerHTML = `
                    <p>Processing file: ${data.filename}</p>
                    <p>Task ID: ${data.task_id}</p>
                `;
            }
            pollForResults(data.task_id);
        } else {
            const errorMsg = `Error: ${data.error || 'Unknown error'}`;
            if (statusContainer) statusContainer.innerHTML = `<p class="error">${errorMsg}</p>`;
            if (uploadButton) uploadButton.disabled = false;
        }
    } catch (error) {
        const errorMsg = `Error: ${error.message}`;
        if (statusContainer) statusContainer.innerHTML = `<p class="error">${errorMsg}</p>`;
        if (uploadButton) uploadButton.disabled = false;
    }
}
