// Step 2 Parse & Clean JS

document.addEventListener('DOMContentLoaded', () => {
  const fileListTable = document.getElementById('file-list-table');
  const fileListEmpty = document.getElementById('file-list-empty');
  const btnParseCleanTop = document.getElementById('btn-parse-clean-top');
  const btnParseCleanBottom = document.getElementById('btn-parse-clean-bottom');
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

  function doParseClean() {
    btnParseCleanTop.disabled = true;
    btnParseCleanBottom.disabled = true;
    parseResults.textContent = 'Parsing and cleaning...';
    fetch('/api/step2/parse_clean', {method: 'POST'}).then(r => r.json()).then(data => {
      btnParseCleanTop.disabled = false;
      btnParseCleanBottom.disabled = false;
      const results = data.results || [];
      if (!results.length) {
        parseResults.textContent = 'No files parsed.';
        return;
      }
      parseResults.innerHTML = '<b>Parse/Clean Results:</b><ul>' + results.map(r => `<li>${r.file} → ${r.result}</li>`).join('') + '</ul>';
    });
  }

  btnParseCleanTop.addEventListener('click', doParseClean);
  btnParseCleanBottom.addEventListener('click', doParseClean);

  refreshFileList();
});
