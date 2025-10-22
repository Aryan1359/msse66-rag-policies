// step1_upload.js: Handles drag-drop, upload, file list, delete, open

const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const btnUpload = document.getElementById('btn-upload');
const uploadMsg = document.getElementById('upload-msg');
const uploadQueue = document.getElementById('upload-queue');
const fileListTable = document.getElementById('file-list-table');
const fileListEmpty = document.getElementById('file-list-empty');

function humanSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
  if (bytes < 1024*1024*1024) return (bytes/1024/1024).toFixed(1) + ' MB';
  return (bytes/1024/1024/1024).toFixed(1) + ' GB';
}

function getExt(name) {
  return name.split('.').pop().toLowerCase();
}

function showMsg(msg, type='muted') {
  uploadMsg.textContent = msg;
  uploadMsg.className = type;
}

function refreshFileList() {
  fetch('/api/files').then(r => r.json()).then(data => {
    const files = data.files || [];
    const tbody = fileListTable.querySelector('tbody');
    tbody.innerHTML = '';
    if (!files.length) {
      fileListEmpty.style.display = '';
      fileListTable.style.display = 'none';
      return;
    }
    fileListEmpty.style.display = 'none';
    fileListTable.style.display = '';
    files.forEach(f => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${f.name}</td>
        <td>${getExt(f.name)}</td>
        <td>${f.size ? humanSize(f.size) : '?'}</td>
        <td>${f.mtime ? new Date(f.mtime*1000).toLocaleString() : '—'}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="window.open('/api/files/raw/${encodeURIComponent(f.name)}', '_blank')">Open</button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteFile('${encodeURIComponent(f.name)}')">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  });
}

function deleteFile(name) {
  if (!confirm('Delete this file?')) return;
  fetch(`/api/files/${name}`, { method: 'DELETE' })
    .then(r => r.json())
    .then(data => {
      if (data.error) showMsg('Delete failed: ' + data.error, 'text-danger');
      else showMsg('File deleted.', 'text-success');
      refreshFileList();
    })
    .catch(() => showMsg('Delete failed.', 'text-danger'));
}

function uploadFiles(files) {
  if (!files.length) return;
  btnUpload.disabled = true;
  showMsg('Uploading...');
  uploadQueue.innerHTML = '';
  let done = 0;
  Array.from(files).forEach(file => {
    const fd = new FormData();
    fd.append('file', file);
    const row = document.createElement('div');
    row.textContent = `Uploading ${file.name}...`;
    uploadQueue.appendChild(row);
    fetch('/api/files', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(data => {
        row.textContent = `Uploaded ${file.name}`;
        done++;
        if (done === files.length) {
          btnUpload.disabled = false;
          showMsg('Upload complete.', 'text-success');
          refreshFileList();
        }
      })
      .catch(() => {
        row.textContent = `Failed: ${file.name}`;
        btnUpload.disabled = false;
        showMsg('Upload failed.', 'text-danger');
      });
  });
}

// Drag & drop
uploadZone.addEventListener('dragover', e => {
  e.preventDefault();
  uploadZone.style.background = '#eef2ff';
});
uploadZone.addEventListener('dragleave', e => {
  e.preventDefault();
  uploadZone.style.background = '#f9fafb';
});
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.style.background = '#f9fafb';
  if (e.dataTransfer.files.length) {
    uploadFiles(e.dataTransfer.files);
  }
});

btnUpload.addEventListener('click', () => {
  fileInput.click();
});
fileInput.addEventListener('change', () => {
  uploadFiles(fileInput.files);
});

refreshFileList();
