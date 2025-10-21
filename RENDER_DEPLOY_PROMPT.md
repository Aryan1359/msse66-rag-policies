# Render Deployment & Verification Prompt for Copilot

Paste this into Copilot at the start of your next session to guide deployment and verification on Render:

---

**STEP A: Deploy to Render**
1. Open the Render dashboard and create a new Web Service.
2. Connect your GitHub repo: `Aryan1359/msse66-rag-policies`.
3. Set the build and start commands:
   - Build: `pip install -r requirements.txt`
   - Start: `python app.py`
4. Set environment: Python 3.10+ (or as required by `runtime.txt`).
5. Deploy and wait for the service to build and start.
6. Copy the live service URL and paste it here.

*Copilot: Wait for the user to paste the Render service URL before continuing.*

---

**STEP B: Verify Health Endpoint**
1. Run: `curl -sSL <RENDER_URL>/health`
2. If response is not `{"status":"ok"}` or fails, diagnose and suggest one fix.
3. Wait for user confirmation before proceeding.

---

**STEP C: Verify /ask Endpoint**
1. Run: `curl -sSL -X POST <RENDER_URL>/ask -H 'Content-Type: application/json' -d '{"question": "What is the PTO policy?"}'`
2. If response is not as expected, diagnose and suggest one fix.
3. Wait for user confirmation before proceeding.

---

**STEP D: Update README**
1. Append the Render live URL to `README.md` under a new section: `## Live Demo`
2. Commit with message: `docs: add Render live URL`
3. Open a PR to main.

---

*Copilot: After each step, wait for user confirmation before continuing to the next.*
