async function loadFiles() {
	const ul = document.getElementById("file-list");
	if (!ul) return;
	try {
		const r = await fetch("/api/files");
		if (!r.ok) throw new Error("HTTP " + r.status);
		const data = await r.json();
		ul.innerHTML = "";
		if (!data.files || data.files.length === 0) {
			ul.innerHTML = '<li class="muted">No indexed files</li>';
			return;
		}
						for (const f of data.files) {
								const when = f.mtime ? new Date(f.mtime * 1000).toLocaleString() : "—";
								const li = document.createElement("li");
								li.innerHTML = `
									<a href="/api/files/raw/${encodeURIComponent(f.name)}" target="_blank" rel="noopener">
										<strong>${f.name}</strong>
									</a>
									<span class="muted">(${f.chunk_count} chunks, mtime: ${when})</span>
									<button class="danger" data-name="${f.name}" style="margin-left:10px;">Delete</button>
								`;
								ul.appendChild(li);
		}
	} catch (e) {
		ul.innerHTML = `<li class="muted">Failed to load: ${e.message}</li>`;
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
	const ul = document.getElementById("file-list");
	if (ul) {
		ul.addEventListener("click", (ev) => {
			const t = ev.target;
			if (t && t.matches("button.danger[data-name]")) {
				deleteFile(t.getAttribute("data-name"));
			}
		});
	}
});
