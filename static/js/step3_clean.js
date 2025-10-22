// JS for Step 3: List files from Step 2 and trigger clean

document.addEventListener('DOMContentLoaded', function() {
  const fileListTable = document.getElementById('file-list-table');
  const fileListEmpty = document.getElementById('file-list-empty');
  const btnCleanTop = document.getElementById('btn-clean-top');
  const btnCleanBottom = document.getElementById('btn-clean-bottom');
  const cleanResults = document.getElementById('clean-results');

  function fetchFiles() {
  fetch('/api/step3/files')
      .then(res => res.json())
      .then(data => {
        const files = data.files || [];
        const tbody = fileListTable.querySelector('tbody');
        tbody.innerHTML = '';
        if (files.length === 0) {
          fileListTable.style.display = 'none';
          fileListEmpty.style.display = '';
        } else {
          fileListTable.style.display = '';
          fileListEmpty.style.display = 'none';
          files.forEach(f => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${f.name}</td><td>${(f.size/1024).toFixed(1)} KB</td><td>${new Date(f.mtime * 1000).toLocaleString()}</td>`;
            tbody.appendChild(tr);
          });
        }
      })
      .catch(() => {
        fileListEmpty.style.display = '';
        fileListTable.style.display = 'none';
      });
  }

  function cleanAllFiles() {
    btnCleanTop.disabled = true;
    btnCleanBottom.disabled = true;
    cleanResults.innerHTML = '<div class="alert alert-info">Cleaning files...</div>';
    fetch('/api/step3/clean', { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        let html = '';
        if (data.results && data.results.length > 0) {
          html += '<h3>Clean Results</h3><ul>';
          data.results.forEach(r => {
            html += `<li>File <b>${r.doc_id}</b> cleaned and saved in <code>${r.cleaned_path}</code></li>`;
          });
          html += '</ul>';
        } else {
          html += '<div class="alert alert-warning">No files cleaned.</div>';
        }
        cleanResults.innerHTML = html;
        btnCleanTop.disabled = false;
        btnCleanBottom.disabled = false;
        fetchFiles();
      })
      .catch(() => {
        cleanResults.innerHTML = '<div class="alert alert-danger">Error cleaning files.</div>';
        btnCleanTop.disabled = false;
        btnCleanBottom.disabled = false;
      });
  }

  btnCleanTop.addEventListener('click', cleanAllFiles);
  btnCleanBottom.addEventListener('click', cleanAllFiles);

  fetchFiles();
});
