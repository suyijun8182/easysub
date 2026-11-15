import os
import re
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


@router.get("/library/{slug}")
def library_icon(slug: str):
    """返回某个商家图标；本地无缓存时从公共 favicon 服务下载后缓存。"""
    safe = re.sub(r"[^A-Za-z0-9_.\-]", "", slug)
    if not safe.endswith(".png"):
        safe += ".png"
    path = os.path.join(LIBRARY_DIR, safe)
    if os.path.isfile(path):
        return FileResponse(path)

    domain = icon_library.domain_for_slug(safe)
    if not domain:
        raise HTTPException(404, "未知图标")
    # 用 Google favicon 服务抓取该商家图标（覆盖面广、稳定）
    fav = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    try:
        resp = httpx.get(fav, timeout=12, follow_redirects=True)
        resp.raise_for_status()
        os.makedirs(LIBRARY_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(resp.content)
        return Response(content=resp.content, media_type="image/png")
    except Exception:  # noqa: BLE001
        # 下载失败返回 1x1 透明占位，避免前端报错
        raise HTTPException(404, "图标暂不可用")
