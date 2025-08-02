const BACKEND_URL = "http://127.0.0.1:5000"; // ✅ Flask backend URL

function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));

    document.querySelector(`.tab[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');

    // ✅ Load file list only for Save/Delete tabs
    if (tabName === 'save' || tabName === 'delete') {
        loadFileLists();
    }
}

function uploadFiles() {
    const folderInput = document.getElementById('folderInput');
    const fileInput = document.getElementById('fileInput');

    const folderFiles = folderInput.files;
    const individualFiles = fileInput.files;

    if (folderFiles.length === 0 && individualFiles.length === 0) {
        alert("Please select a folder or files to upload.");
        return;
    }

    const formData = new FormData();

    for (let file of folderFiles) {
        formData.append('files', file);
    }

    for (let file of individualFiles) {
        formData.append('files', file);
    }

    fetch(`${BACKEND_URL}/upload`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(msg => {
        alert(msg);
        loadFileLists(); // refresh after upload
    })
    .catch(error => alert("Upload failed: " + error));
}

function saveToLocal() {
    fetch(`${BACKEND_URL}/download`)
        .then(response => {
            if (!response.ok) throw new Error("Download failed");
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'can_data_export.zip';
            a.click();
        })
        .catch(error => alert("Download failed: " + error));
}

function deleteFromDatabase() {
    if (!confirm("Are you sure you want to delete ALL CAN data from MySQL?")) return;

    fetch(`${BACKEND_URL}/delete`, {
        method: 'DELETE'
    })
    .then(response => response.text())
    .then(msg => {
        alert(msg);
        loadFileLists(); // refresh after deletion
    })
    .catch(error => alert("Delete failed: " + error));
}

// ✅ NEW: Delete a single file by ID
function deleteOne(fileId) {
    if (!confirm("Delete this file from MySQL?")) return;

    fetch(`${BACKEND_URL}/delete/${fileId}`, {
        method: 'DELETE'
    })
    .then(res => res.text())
    .then(msg => {
        alert(msg);
        loadFileLists();
    })
    .catch(err => alert("Delete failed: " + err));
}

function downloadOne(fileId, filename) {
    fetch(`${BACKEND_URL}/download/${fileId}`)
        .then(res => {
            if (!res.ok) throw new Error("Failed to download file");
            return res.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
        })
        .catch(err => alert("Download failed: " + err));
}


// ✅ NEW: Load file list for Save and Delete tab
function loadFileLists() {
    fetch(`${BACKEND_URL}/files`)
        .then(res => res.json())
        .then(files => {
            const saveTable = document.getElementById('saveFileList').querySelector('tbody');
            const deleteTable = document.getElementById('deleteFileList').querySelector('tbody');
            saveTable.innerHTML = '';
            deleteTable.innerHTML = '';

            if (files.length === 0) {
                saveTable.innerHTML = '<tr><td colspan="2">No files available.</td></tr>';
                deleteTable.innerHTML = '<tr><td colspan="2">No files available.</td></tr>';
                return;
            }

            files.forEach(file => {
                const saveRow = document.createElement('tr');
                saveRow.innerHTML = `
                    <td>${file.filename}</td>
                    <td><button onclick="downloadOne(${file.id}, '${file.filename}')">⬇️ Download</button></td>
                `;
                saveTable.appendChild(saveRow);

                const deleteRow = document.createElement('tr');
                deleteRow.innerHTML = `
                    <td>${file.filename}</td>
                    <td><button onclick="deleteOne(${file.id})">❌ Delete</button></td>
                `;
                deleteTable.appendChild(deleteRow);
            });
        })
        .catch(error => console.error("Failed to load file list:", error));
}
