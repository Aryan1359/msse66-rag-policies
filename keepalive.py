# keepalive.py
import os, threading, time, json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone

_state = {
    "enabled": False,
    "url": None,
    "interval_sec": 540,
    "last_ok_utc": None,
    "last_err_utc": None,
    "last_status": None,
}

def _now_utc():
    return datetime.now(timezone.utc).isoformat()

def _derive_url():
    url = os.environ.get("KEEPALIVE_URL")
    if url:
        return url
    ren = os.environ.get("RENDER_EXTERNAL_URL")
    if ren:
        base = ren.rstrip("/")
        return f"{base}/health"
    port = int(os.environ.get("PORT", "8000"))
    return f"http://127.0.0.1:{port}/health"

def _tick():
    while _state["enabled"]:
        try:
            req = Request(_state["url"], method="GET")
            with urlopen(req, timeout=5) as resp:
                _state["last_status"] = f"{resp.status}"
                _state["last_ok_utc"] = _now_utc()
        except (HTTPError, URLError, TimeoutError) as e:
            _state["last_status"] = f"error:{e}"
            _state["last_err_utc"] = _now_utc()
        except Exception as e:
            _state["last_status"] = f"error:{type(e).__name__}"
            _state["last_err_utc"] = _now_utc()
        time.sleep(_state["interval_sec"])

def start_if_enabled(app_logger=None):
    enabled = os.environ.get("KEEPALIVE_ENABLED", "").lower() in ("1","true","yes","on")
    _state["enabled"] = enabled
    _state["url"] = _derive_url()
    if app_logger:
        app_logger.info("keepalive: enabled=%s url=%s interval=%ss",
                        enabled, _state["url"], _state["interval_sec"])
    if not enabled:
        return
    t = threading.Thread(target=_tick, daemon=True)
    t.start()

def status_json():
    return json.dumps({
        "enabled": _state["enabled"],
        "url": _state["url"],
        "interval_sec": _state["interval_sec"],
        "last_ok_utc": _state["last_ok_utc"],
        "last_err_utc": _state["last_err_utc"],
        "last_status": _state["last_status"],
    })
