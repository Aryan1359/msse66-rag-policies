async function loadFiles() {
	const table = document.getElementById("file-list");
	if (!table) return;
	console.log("loadFiles called");
	let tbody = table.querySelector("tbody");
	if (!tbody) {
		tbody = document.createElement("tbody");
		table.appendChild(tbody);
	}
	try {
		const r = await fetch("/api/files");
		if (!r.ok) throw new Error("HTTP " + r.status);
		const data = await r.json();
		tbody.innerHTML = "";
		if (!data.files || data.files.length === 0) {
			tbody.innerHTML = '<tr><td colspan="4" class="muted" style="text-align:center;">No indexed files</td></tr>';
			return;
		}
		for (const f of data.files) {
			const name = (f.name || "").trim();
			const when = f.mtime ? new Date(f.mtime * 1000).toLocaleString() : "—";
			const tr = document.createElement("tr");
			tr.innerHTML = `
				<td style="padding:6px 8px;">
					<a href="/api/files/raw/${encodeURIComponent(name)}" target="_blank" rel="noopener">
						<strong>${name}</strong>
					</a>
				</td>
				<td style="text-align:center; padding:6px 8px;">${f.chunk_count}</td>
				<td style="text-align:center; padding:6px 8px;">${when}</td>
				<td style="text-align:center; padding:6px 8px;">
					<button class="danger" data-name="${name}" title="Delete" style="border:none; background:none; padding:0; cursor:pointer;">
						<span style="font-size:18px; color:#991b1b;">&#128465;</span>
					</button>
				</td>
			`;
			tbody.appendChild(tr);
		}
	} catch (e) {
		tbody.innerHTML = `<tr><td colspan="4" class="muted" style="text-align:center;">Failed to load: ${e.message}</td></tr>`;
	}
}

async function uploadFile() {
	const inp = document.getElementById("upload-file");
	const msg = document.getElementById("upload-msg");
	if (!inp || !inp.files || inp.files.length === 0) {
		if (msg) msg.textContent = "Choose a file first.";
		return;
	}
	const fd = new FormData();
	fd.append("file", inp.files[0]);
	try {
		const r = await fetch("/api/files", { method: "POST", body: fd });
		const text = await r.text(); // tolerate non-JSON errors
		let data = null;
		try { data = JSON.parse(text); } catch {}
		if (!r.ok) throw new Error((data && data.error) || text || `HTTP ${r.status}`);
		if (msg) msg.textContent = `Uploaded. Indexed files: ${data?.count ?? "?"}`;
		loadFiles();
		inp.value = "";
	} catch (e) {
		if (msg) msg.textContent = `Upload failed: ${e.message}`;
	}
}


async function deleteFile(name) {
	if (!name) return;
	if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
	try {
		const r = await fetch(`/api/files/${encodeURIComponent(name)}`, { method: "DELETE" });
		const text = await r.text();
		let data = null;
		try { data = JSON.parse(text); } catch {}
		if (!r.ok) throw new Error((data && data.error) || text || `HTTP ${r.status}`);
		await loadFiles();
	} catch (e) {
		alert(`Delete failed: ${e.message}`);
	}
}

document.addEventListener("DOMContentLoaded", () => {
	loadFiles();
	const btn = document.getElementById("btn-upload");
	if (btn) btn.addEventListener("click", uploadFile);
	const table = document.getElementById("file-list");
	if (table) {
		table.addEventListener("click", (ev) => {
			const t = ev.target.closest("button.danger[data-name]");
			if (t) {
				deleteFile(t.getAttribute("data-name"));
			}
		});
	}

	// Ask a Question logic
	const askBtn = document.getElementById("btn-ask");
	const qBox = document.getElementById("q");
	const answerDiv = document.getElementById("answer");
	if (askBtn && qBox && answerDiv) {
		askBtn.addEventListener("click", async () => {
			const question = qBox.value.trim();
			if (!question) {
				answerDiv.textContent = "Please enter a question.";
				return;
			}
			askBtn.disabled = true;
			answerDiv.textContent = "Thinking...";
			try {
				const r = await fetch("/ask", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ question })
				});
				const text = await r.text();
				let data = null;
				try { data = JSON.parse(text); } catch {}
				if (!r.ok) throw new Error((data && data.error) || text || `HTTP ${r.status}`);
				// Format answer and sources
				let html = "";
				html += `<div style='font-size:16px; margin-bottom:10px;'><strong>Answer:</strong><br>${data.answer || "No answer."}</div>`;
				if (data.sources && data.sources.length > 0) {
					html += `<div style='margin-top:8px;'><strong>Sources:</strong><ul style='margin:6px 0 0 16px; padding:0;'>`;
					for (const s of data.sources) {
						html += `<li>[${s.label}] <span style='color:#374151;'>doc_id:</span> <code>${s.doc_id}</code>, <span style='color:#374151;'>chunk_id:</span> <code>${s.chunk_id}</code></li>`;
					}
					html += `</ul></div>`;
				}
				answerDiv.innerHTML = html;
			} catch (e) {
				answerDiv.textContent = `Error: ${e.message}`;
			} finally {
				askBtn.disabled = false;
			}
		});
	}
});
	const askBtn = document.getElementById("btn-ask");
	const qBox = document.getElementById("q");
	const answerDiv = document.getElementById("answer");
	if (askBtn && qBox && answerDiv) {
		askBtn.addEventListener("click", async () => {
			const question = qBox.value.trim();
			if (!question) {
				answerDiv.textContent = "Please enter a question.";
				return;
			}
			askBtn.disabled = true;
			answerDiv.textContent = "Thinking...";
			try {
				const r = await fetch("/ask", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ question })
				});
				const text = await r.text();
				let data = null;
				try { data = JSON.parse(text); } catch {}
				if (!r.ok) throw new Error((data && data.error) || text || `HTTP ${r.status}`);
				answerDiv.textContent = data.answer || "No answer.";
			} catch (e) {
				answerDiv.textContent = `Error: ${e.message}`;
			} finally {
				askBtn.disabled = false;
			}
		});
	}
