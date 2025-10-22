// Step 2 Parse & Clean JS

document.addEventListener('DOMContentLoaded', () => {
  const table = document.getElementById('parse-table');
  const btnParseAll = document.getElementById('btn-parse-all');
  const btnCleanAll = document.getElementById('btn-clean-all');
  const btnParseCleanAll = document.getElementById('btn-parse-clean-all');
  const resultMsg = document.getElementById('result-msg');

  function showMsg(msg, type='info') {
    resultMsg.textContent = msg;
    resultMsg.className = 'muted';
    if (type === 'error') resultMsg.className = 'text-danger';
    if (type === 'success') resultMsg.className = 'text-success';
  }

  function fetchStats() {
    fetch('/api/parse/stats').then(r => r.json()).then(data => {
      const tbody = table.querySelector('tbody');
      tbody.innerHTML = '';
      (data || []).forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${f.doc_id}</td>
          <td>${f.ext}</td>
          <td>${f.status}</td>
          <td>${f.chars}</td>
          <td>${f.words}</td>
          <td>${f.last_parsed_iso || '—'}</td>
          <td>
            <button class='btn btn-sm btn-primary' onclick="runParse('${f.doc_id}')">Parse</button>
            <button class='btn btn-sm btn-warning' onclick="runClean('${f.doc_id}')">Clean</button>
            <button class='btn btn-sm btn-success' onclick="runParseClean('${f.doc_id}')">Parse+Clean</button>
            <button class='btn btn-sm btn-outline-secondary' onclick="runPreview('${f.doc_id}')">Preview</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    });
  }

  window.runParse = function(docId) {
    showMsg('Parsing ' + docId + ' ...');
    fetch('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_ids: [docId] })
    }).then(r => r.json()).then(res => {
      if (res.parsed && res.parsed.includes(docId)) {
        showMsg('Parse ' + docId + ': Success', 'success');
      } else {
        showMsg('Parse ' + docId + ': ' + (res.errors[0]?.error || 'Error'), 'error');
      }
      fetchStats();
    });
  }

  window.runClean = function(docId) {
    showMsg('Cleaning ' + docId + ' ...');
    fetch('/api/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_ids: [docId] })
    }).then(r => r.json()).then(res => {
      if (res.cleaned && res.cleaned.includes(docId)) {
        showMsg('Clean ' + docId + ': Success', 'success');
      } else {
        showMsg('Clean ' + docId + ': ' + (res.errors[0]?.error || 'Error'), 'error');
      }
      fetchStats();
    });
  }

  window.runParseClean = function(docId) {
    showMsg('Parse+Clean ' + docId + ' ...');
    fetch('/api/parse_clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_ids: [docId] })
    }).then(r => r.json()).then(res => {
      const r = res[0];
      if (r && r.parse && r.clean && r.clean.status === 'cleaned') {
        showMsg('Parse+Clean ' + docId + ': Success', 'success');
      } else {
        showMsg('Parse+Clean ' + docId + ': ' + (r.error || r.parse?.error || 'Error'), 'error');
      }
      fetchStats();
    });
  }

  window.runPreview = function(docId) {
    showMsg('Loading preview ...');
    fetch(`/api/parsed/${encodeURIComponent(docId)}`)
      .then(r => {
        if (!r.ok) throw new Error('Not parsed yet');
        return r.text();
      })
      .then(txt => {
        document.getElementById('previewContent').textContent = txt;
        const modalEl = document.getElementById('previewModal');
        if (window.bootstrap && bootstrap.Modal) {
          let modal = bootstrap.Modal.getOrCreateInstance(modalEl);
          modal.show();
        } else {
          modalEl.style.display = 'block';
        }
        showMsg('Preview loaded.', 'success');
      })
      .catch((err) => {
        document.getElementById('previewContent').textContent = 'Preview not available.';
        showMsg('Failed to load preview: ' + err.message, 'error');
      });
  }

  btnParseAll.onclick = function() {
    showMsg('Parsing all files ...');
    fetch('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    }).then(r => r.json()).then(res => {
      showMsg('Parse All: ' + (res.parsed?.length || 0) + ' parsed, ' + (res.errors?.length || 0) + ' errors.', res.errors?.length ? 'error' : 'success');
      fetchStats();
    });
  }

  btnCleanAll.onclick = function() {
    showMsg('Cleaning all files ...');
    fetch('/api/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    }).then(r => r.json()).then(res => {
      showMsg('Clean All: ' + (res.cleaned?.length || 0) + ' cleaned, ' + (res.errors?.length || 0) + ' errors.', res.errors?.length ? 'error' : 'success');
      fetchStats();
    });
  }

  btnParseCleanAll.onclick = function() {
    showMsg('Parse+Clean all files ...');
    fetch('/api/parse_clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    }).then(r => r.json()).then(res => {
      let ok = res.filter(r => r.clean && r.clean.status === 'cleaned').length;
      let err = res.length - ok;
      showMsg('Parse+Clean All: ' + ok + ' ok, ' + err + ' errors.', err ? 'error' : 'success');
      fetchStats();
    });
  }

  fetchStats();
});
