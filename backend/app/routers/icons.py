import html
import os
import re
import threading
import time
import uuid

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app import icon_library, outbound
from app.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/api/icons", tags=["icons"])

UPLOAD_DIR = os.path.join("data", "icons")
LIBRARY_DIR = os.path.join("data", "icons", "library")
ALLOWED = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".ico"}
MAX_BYTES = 2 * 1024 * 1024  # 2MB
# 镜像和源码里已经带着的图标（前端 public/preview-icons，构建时复制进 frontend_dist）
BUNDLED_DIRS = (
    os.path.join("frontend_dist", "preview-icons"),
    os.path.join("..", "frontend", "public", "preview-icons"),
)
FETCH_TIMEOUT = 4
FAILURE_TTL = 6 * 3600
PLACEHOLDER_HEADERS = {"Cache-Control": "public, max-age=86400"}
# 进程内记录下载失败的图标，避免访问不到外网时每次打开页面都等待超时
_failed: dict[str, float] = {}
_client: httpx.Client | None = None
_client_lock = threading.Lock()


def _favicon_client() -> httpx.Client:
    # 复用一个客户端：每次新建都要重新加载证书，在 Windows 上要 1～2 秒，会让 4 秒超时变成 6 秒。
    # 首次使用时才创建，仍会读取环境变量里的 HTTPS_PROXY。
    global _client
    with _client_lock:
        if _client is None:
            _client = httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=True)
        return _client


def _fetch_favicon(domain: str) -> bytes:
    resp = _favicon_client().get(f"https://www.google.com/s2/favicons?domain={domain}&sz=64")
    resp.raise_for_status()
    return resp.content


class IconUrlIn(BaseModel):
    url: str


@router.post("/upload")
async def upload_icon(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    """用户上传本地图标。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"不支持的图标格式：{ext}")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "图标过大（上限 2MB）")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9_.\-]", "", f"{user.id}_{uuid.uuid4().hex}{ext}")
    with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
        f.write(data)
    return {"url": f"/static/icons/{name}"}


@router.post("/from-url")
def import_from_url(payload: IconUrlIn, user: User = Depends(get_current_user)):
    """从 URL 下载图标并保存到本地。"""
    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "请输入 http(s) 图标地址")
    try:
        content = bytearray()
        with outbound.client(timeout=15, follow_redirects=True) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                ctype = response.headers.get("content-type", "")
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > MAX_BYTES:
                        raise ValueError("图标过大（上限 2MB）")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, outbound.error_summary(e))

    ext = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/x-icon": ".ico",
        "image/vnd.microsoft.icon": ".ico",
    }.get(ctype.split(";")[0].strip(), os.path.splitext(url)[1].lower() or ".png")
    if ext not in ALLOWED:
        ext = ".png"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    name = f"{user.id}_{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
        f.write(bytes(content))
    return {"url": f"/static/icons/{name}"}


@router.get("/library")
def list_library(user: User = Depends(get_current_user)):
    """内置常见商家图标库清单（也用于服务名联想）。"""
    return icon_library.manifest()


def placeholder_svg(name: str) -> str:
    letter = html.escape((name or "?").strip()[:1] or "?")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#e3f3ec"/>'
        f'<text x="32" y="43" text-anchor="middle" fill="#12805c" font-size="36" font-family="sans-serif">{letter}</text>'
        "</svg>"
    )


def _contained(directory: str, name: str) -> str | None:
    root = os.path.realpath(directory)
    candidate = os.path.realpath(os.path.join(root, name))
    try:
        inside = os.path.commonpath([root, candidate]) == root
    except ValueError:
        return None
    return candidate if inside and os.path.isfile(candidate) else None


@router.get("/library/{slug}")
def library_icon(slug: str):
    """返回商家图标：下载缓存 → 内置图标 → 网络下载；下载失败返回首字母占位图。"""
    safe = re.sub(r"[^A-Za-z0-9_.\-]", "", slug)
    if not safe.endswith(".png"):
        safe += ".png"
    for directory in (LIBRARY_DIR, *BUNDLED_DIRS):
        found = _contained(directory, safe)
        if found:
            return FileResponse(found)

    domain = icon_library.domain_for_slug(safe)
    if not domain:
        raise HTTPException(404, "未知图标")
    entry = next((e for e in icon_library.manifest() if e["domain"] == domain), None)
    placeholder = Response(
        content=placeholder_svg(entry["name"] if entry else domain),
        media_type="image/svg+xml",
        headers=PLACEHOLDER_HEADERS,
    )
    failed_at = _failed.get(safe)
    if failed_at is not None and time.monotonic() - failed_at < FAILURE_TTL:
        return placeholder
    # 用 Google favicon 服务抓取该商家图标（覆盖面广；大陆网络通常访问不到，所以超时要短）
    try:
        content = _fetch_favicon(domain)
    except Exception:  # noqa: BLE001
        _failed[safe] = time.monotonic()
        return placeholder
    _failed.pop(safe, None)
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    with open(os.path.join(LIBRARY_DIR, safe), "wb") as f:
        f.write(content)
    return Response(content=content, media_type="image/png")
