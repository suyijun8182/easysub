"""Cache the existing service directory's public favicons for offline UI previews."""
import concurrent.futures
import json
from pathlib import Path
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parents[1]
catalog = json.loads((root / "src/android-preview/seed.json").read_text(encoding="utf-8"))["catalog"]
destination = root / "public/preview-icons"
destination.mkdir(exist_ok=True)


def cache(service):
    path = destination / (service["slug"] + ".png")
    local = root.parent / "backend/data/icons/library" / path.name
    if path.exists():
        return service["slug"]
    try:
        if local.exists():
            data = local.read_bytes()
        else:
            url = "https://www.google.com/s2/favicons?" + urllib.parse.urlencode({"domain": service["domain"], "sz": 64})
            request = urllib.request.Request(url, headers={"User-Agent": "EasySub-Design-Preview/1.0"})
            with urllib.request.urlopen(request, timeout=8) as response:
                data = response.read(100_001)
        if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) > 100_000:
            return None
        path.write_bytes(data)
        return service["slug"]
    except (OSError, ValueError):
        return None


with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
    available = sorted(set(filter(None, executor.map(cache, catalog))))
(root / "src/android-preview/cached-icons.json").write_text(json.dumps(available, indent=2), encoding="utf-8")
print(f"Cached {len(available)} of {len(catalog)} service favicons; remaining services keep explicit initials.")
