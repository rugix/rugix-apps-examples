import json
import os
import urllib.request

port = int(os.environ.get("API_PORT", "8080"))
with urllib.request.urlopen(f"http://127.0.0.1:{port}/samples/latest", timeout=3) as response:
    data = json.loads(response.read().decode("utf-8"))

if data["count"] < 1 or not data["samples"]:
    raise SystemExit("no historian samples")

print(json.dumps(data["samples"][0], sort_keys=True))

