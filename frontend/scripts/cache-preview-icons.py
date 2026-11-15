"""Cache the service directory's public favicons as bundled 64x64 PNGs.

The backend serves these from the image before trying the network (issue #2),
so run this after adding services to the icon library. Requires Pillow
(developer machine only; not an app dependency).
"""
import concurrent.futures
import io
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

try:
    from PIL import Image
except ImportError:  # pragma: no cover - developer tool
    raise SystemExit("pip install pillow  # only needed to run this script")

root = Path(__file__).resolve().parents[1]
catalog = json.loads((root / "src/android-preview/seed.json").read_text(encoding="utf-8"))["catalog"]
destination = root / "public/preview-icons"
destination.mkdir(exist_ok=True)
SIZE = 64


def sources(domain):
    yield "https://www.google.com/s2/favicons?" + urllib.parse.urlencode({"domain": domain, "sz": SIZE})
    yield f"https://icons.duckduckgo.com/ip3/{domain}.ico"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "EasySub-Icon-Cache/1.0"})
    # Both services answer unknown domains with a 404 placeholder image; urlopen raises on it.
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read(500_001)


def to_png(data):
    if len(data) > 500_000:
        raise ValueError("too large")
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        frame = image.convert("RGBA")
    if frame.size != (SIZE, SIZE):
        frame = frame.resize((SIZE, SIZE), Image.LANCZOS)
    out = io.BytesIO()
    frame.save(out, "PNG", optimize=True)
    return out.getvalue()


def cache(service):
    path = destination / (service["slug"] + ".png")
    if path.exists():
        return service["slug"], "kept"
    local = root.parent / "backend/data/icons/library" / path.name
    candidates = [local.read_bytes()] if local.exists() else []
    for url in sources(service["domain"]):
        try:
            candidates.append(fetch(url))
        except (OSError, ValueError, urllib.error.HTTPError):
            continue
    for data in candidates:
        try:
            path.write_bytes(to_png(data))
            return service["slug"], "fetched"
        except (OSError, ValueError, Image.DecompressionBombError):
            continue
    return service["slug"], "missing"


with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
    results = dict(executor.map(cache, catalog))
available = sorted(slug for slug, state in results.items() if state != "missing")
(root / "src/android-preview/cached-icons.json").write_text(json.dumps(available, indent=2), encoding="utf-8")
fetched = sorted(slug for slug, state in results.items() if state == "fetched")
missing = sorted(slug for slug, state in results.items() if state == "missing")
print(f"Bundled {len(available)} of {len(catalog)} service icons; fetched now: {fetched}")
print(f"Not available from any source (add to EXEMPT in backend/tests/test_bundled_icons.py): {missing}")
