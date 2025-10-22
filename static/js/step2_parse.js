// step2_parse.js: Handles parse all, stats table, preview modal

document.addEventListener('DOMContentLoaded', () => {
  const table = document.getElementById('parse-table');
  const btnParseAll = document.getElementById('btn-parse-all');
  const parseMsg = document.getElementById('parse-msg');
  const previewModal = document.getElementById('previewModal');
  const previewContent = document.getElementById('previewContent');

  function fetchStats() {
    fetch('/api/step2/files').then(r => r.json()).then(data => {
      const tbody = table.querySelector('tbody');
      tbody.innerHTML = '';
      (data || []).forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td></td>
          <td>${f.doc_id}</td>
          <td>${f.ext}</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td><button class='btn btn-sm btn-outline-primary' data-preview='${f.doc_id}'>Preview</button></td>
        `;
        tbody.appendChild(tr);
      });
    });
  }

  btnParseAll.addEventListener('click', () => {
    btnParseAll.disabled = true;
    parseMsg.textContent = 'Parsing...';
    fetch('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
      .then(r => r.json())
      .then(data => {
        parseMsg.textContent = `Parsed: ${data.parsed.length}, Errors: ${data.errors.length}`;
        btnParseAll.disabled = false;
        fetchStats();
      })
      .catch(() => {
        parseMsg.textContent = 'Parse failed.';
        btnParseAll.disabled = false;
      });
  });

  table.addEventListener('click', e => {
    const btn = e.target.closest('button[data-preview]');
    if (btn) {
      const docId = btn.getAttribute('data-preview');
      previewContent.textContent = 'Loading...';
      fetch(`/api/parsed/${encodeURIComponent(docId)}`)
        .then(r => r.text())
        .then(txt => {
          previewContent.textContent = txt.slice(0, 2000);
          new bootstrap.Modal(previewModal).show();
        })
        .catch(() => {
          previewContent.textContent = 'Failed to load preview.';
          new bootstrap.Modal(previewModal).show();
        });
    }
  });

  fetchStats();
});

// JS for Step 2: List files from Step 1 and trigger parse

document.addEventListener('DOMContentLoaded', function() {
  const fileListTable = document.getElementById('file-list-table');
  const fileListEmpty = document.getElementById('file-list-empty');
  const btnParseTop = document.getElementById('btn-parse-top');
  const btnParseBottom = document.getElementById('btn-parse-bottom');
  const parseResults = document.getElementById('parse-results');

  function refreshFileList() {
    fetch('/api/step2/files').then(r => r.json()).then(data => {
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
        tr.innerHTML = `<td>${f.name}</td><td>${(f.size/1024).toFixed(1)} KB</td><td>${new Date(f.mtime * 1000).toLocaleString()}</td>`;
        tbody.appendChild(tr);
      });
    }).catch(() => {
      fileListEmpty.style.display = '';
      fileListTable.style.display = 'none';
    });
  }

  function doParse() {
    btnParseTop.disabled = true;
    btnParseBottom.disabled = true;
    parseResults.textContent = 'Parsing...';
    fetch('/api/step2/parse', {method: 'POST'}).then(r => r.json()).then(data => {
      btnParseTop.disabled = false;
      btnParseBottom.disabled = false;
      const results = data.results || [];
      if (!results.length) {
        parseResults.textContent = 'No files parsed.';
        return;
      }
  parseResults.innerHTML = '<b>Parse Results:</b><ul>' + results.map(r => `<li>${r.doc_id} → ${r.parsed_raw_path}</li>`).join('') + '</ul>';
    });
  }

  btnParseTop.addEventListener('click', doParse);
  btnParseBottom.addEventListener('click', doParse);

  refreshFileList();
});
