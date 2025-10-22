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
