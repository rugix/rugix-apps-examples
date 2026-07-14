import json
import os
import urllib.request

port = int(os.environ.get("API_PORT", "8080"))
with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as response:
    data = json.loads(response.read().decode("utf-8"))

if data.get("status") != "ok":
    raise SystemExit(1)

