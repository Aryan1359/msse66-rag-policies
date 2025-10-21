Amazing—POST works and the file shows up. Let’s quickly sanity-check the UI, then add delete.

---

# Quick UI sanity (no code changes)

**Paste to Copilot Chat (optional, just to confirm the page loads JS and renders list):**

> **Copilot, confirm the UI loads and shows files:**
>
> ```bash
> curl -sS http://127.0.0.1:8000/ | head -n 30
> curl -sS http://127.0.0.1:8000/static/app.js | head -n 5
> ```
>
> Reply: page HTML loads, `app.js` served.

(If you’ve already eyeballed in the browser preview, you can skip.)

---

# Step 4 — Delete files (backend + UI)

## 4.0 — Backend: `DELETE /api/files/<name>`

**Copilot prompt:**

> **Copilot, add a delete endpoint to remove a policy file, reindex, and return the updated list:**
>
> * Path: `DELETE /api/files/<name>`
> * Use `secure_filename` + `os.path.basename` to prevent traversal.
> * Only allow deleting files under `data/policies/`.
> * If not found → 404 JSON. On success → 200 with the same payload as GET.
>
> **Patch `app.py` near Files API block:**
>
> ```python
> @app.route("/api/files/<path:fname>", methods=["DELETE"])
> def api_files_delete(fname):
>     name = secure_filename(os.path.basename(fname))
>     if not name:
>         return jsonify({"ok": False, "error": "invalid name"}), 400
>     p = os.path.join(POLICIES_DIR, name)
>     if not os.path.exists(p):
>         return jsonify({"ok": False, "error": "not found"}), 404
>     # Delete the file
>     try:
>         os.remove(p)
>     except Exception as e:
>         return jsonify({"ok": False, "error": f"delete failed: {e}"}), 500
>     # Rebuild index
>     import subprocess
>     subprocess.run(["python", "scripts/index_jsonl.py"], check=True)
>     # Return updated list
>     return jsonify(_list_files_payload()), 200
> ```
>
> Save `app.py`.

---

## 4.1 — Frontend: add “Delete” buttons and wire JS

**Copilot prompt:**

> **Copilot, update the Files list rendering and add a Delete flow:**
>
> 1. In `templates/base.html` add a small style for danger buttons (optional but nice):
>
> ```html
> <style>
> /* …existing styles… */
> button.danger { background: #991b1b; color: #fff; border-color: #991b1b; }
> </style>
> ```
>
> 2. In `static/app.js`, modify `loadFiles()` to include a Delete button for each item:
>
> ```js
> // inside the loop in loadFiles():
> const when = f.mtime ? new Date(f.mtime * 1000).toLocaleString() : "—";
> const li = document.createElement("li");
> li.innerHTML = `
>   <strong>${f.name}</strong>
>   <span class="muted">(${f.chunk_count} chunks, mtime: ${when})</span>
>   <button class="danger" data-name="${f.name}" style="margin-left:10px;">Delete</button>
> `;
> ul.appendChild(li);
> ```
>
> 3. Still in `static/app.js`, add a delegated click handler on the `<ul>` to handle deletes:
>
> ```js
> async function deleteFile(name) {
>   if (!name) return;
>   if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
>   try {
>     const r = await fetch(`/api/files/${encodeURIComponent(name)}`, { method: "DELETE" });
>    const text = await r.text();
>     let data = null;
>     try { data = JSON.parse(text); } catch {}
>     if (!r.ok) throw new Error((data && data.error) || text || `HTTP ${r.status}`);
>     await loadFiles();
>   } catch (e) {
>     alert(`Delete failed: ${e.message}`);
>   }
> }
>
> document.addEventListener("DOMContentLoaded", () => {
>   loadFiles();
>   const btn = document.getElementById("btn-upload");
>   if (btn) btn.addEventListener("click", uploadFile);
>   const ul = document.getElementById("file-list");
>   if (ul) {
>     ul.addEventListener("click", (ev) => {
>       const t = ev.target;
>       if (t && t.matches("button.danger[data-name]")) {
>         deleteFile(t.getAttribute("data-name"));
>       }
>     });
>   }
> });
> ```
>
> Save `templates/base.html` and `static/app.js`.

---

## 4.2 — Verify via API (upload then delete)

**Copilot prompt:**

> **Copilot, restart server and verify delete path end-to-end:**
>
> ```bash
> pkill -f "flask --app app run" || true
> flask --app app run -p 8000 -h 127.0.0.1 >/tmp/flask.out 2>&1 & sleep 2
>
> # Upload a file we intend to delete
> echo "# Delete Me\n" > /tmp/to_delete.md
> curl -sS -F "file=@/tmp/to_delete.md" http://127.0.0.1:8000/api/files | jq '.files[].name' | sed -n '1,999p'
>
> # Delete it
> curl -sS -X DELETE http://127.0.0.1:8000/api/files/to_delete.md | jq '.files[].name' | sed -n '1,999p'
>
> # Confirm it’s gone
> curl -sS http://127.0.0.1:8000/api/files | jq '.files[].name' | sed -n '1,999p'
> ```
>
> Reply: did we see `to_delete.md` appear after upload, disappear after delete, and remain gone in final GET?

---

## 4.3 — Commit & push

**Copilot prompt:**

> **Copilot, commit and push Step 4:**
>
> ```bash
> git add app.py templates/base.html static/app.js
> git commit -m "feat(ui): delete policies — DELETE /api/files/<name> + UI buttons with confirm()"
> git push
> git log -1 --pretty=oneline
> ```
>
> Confirm the last commit message.

---

When you say **done** (or paste the outputs), I’ll take you to **Step 5 — Q&A panel**: a basic “Ask” form that hits your existing `/search` or `/ask` route and renders results with citations.
