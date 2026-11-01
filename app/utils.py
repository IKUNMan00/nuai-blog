"""通用工具：Markdown 渲染、摘要、图片上传、访客标识等。"""
from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

import bleach
import markdown
from flask import current_app, request
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

# ---------- Markdown ----------

ALLOWED_TAGS = {
    "a", "abbr", "blockquote", "br", "caption", "code", "col", "colgroup", "dd",
    "del", "details", "div", "dl", "dt", "em", "figcaption", "figure", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd", "li", "mark", "ol",
    "p", "pre", "q", "s", "small", "span", "strong", "sub", "summary", "sup",
    "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul", "input",
}
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel", "class"],
    "img": ["src", "alt", "title", "width", "height", "loading", "class"],
    "code": ["class"],
    "pre": ["class"],
    "span": ["class"],
    "div": ["class"],
    "th": ["align", "colspan", "rowspan"],
    "td": ["align", "colspan", "rowspan"],
    "input": ["type", "checked", "disabled"],
    "h1": ["id"], "h2": ["id"], "h3": ["id"], "h4": ["id"], "h5": ["id"], "h6": ["id"],
}
ALLOWED_PROTOCOLS = {"http", "https", "mailto"}


def render_markdown(text: str) -> str:
    """Markdown -> 安全的 HTML。

    先用 Markdown 渲染，再用 bleach 白名单过滤，避免存储型 XSS。
    搜索框、评论等纯文本场景不要调用此函数。
    """
    raw = text or ""
    # 删除明显危险的原始 HTML 块，再进行 Markdown 渲染和白名单过滤
    raw = re.sub(
        r"<(script|style|iframe|object|embed|form)\b[^>]*>.*?</\1\s*>",
        "",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )
    rendered = markdown.markdown(
        raw,
        extensions=["fenced_code", "tables", "sane_lists", "nl2br"],
        output_format="html5",
    )
    cleaned = bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    # 给外链补充安全属性
    cleaned = re.sub(
        r'<a (?![^>]*\brel=)([^>]*href=["\']https?://)',
        r'<a rel="noopener noreferrer" \1',
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned


def summarize(text: str, length: int = 96) -> str:
    """从 Markdown 原文提取纯文本摘要。"""
    value = text or ""
    value = re.sub(r"```.*?```", " ", value, flags=re.DOTALL)
    value = re.sub(r"`[^`]*`", " ", value)
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"^[#>\-\*\d.\s]+", "", value, flags=re.MULTILINE)
    value = re.sub(r"[*_~|]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:length] + ("…" if len(value) > length else "")


def reading_minutes(text: str) -> int:
    return max(1, round(len(text or "") / 400))


# ---------- 图片上传 ----------


class UploadError(ValueError):
    """上传校验失败，路由层捕获后转为用户可读提示。"""


def persist_image(file_storage) -> dict:
    """校验并保存上传图片，返回文件元数据（不写数据库）。"""
    if not file_storage or not file_storage.filename:
        raise UploadError("请选择要上传的图片文件。")

    original_name = Path(file_storage.filename).name[:255]
    data = file_storage.read()
    if not data:
        raise UploadError("文件内容为空，请重新选择。")
    if len(data) > current_app.config["MAX_IMAGE_SIZE"]:
        raise UploadError("图片不能超过 5MB，请压缩后重试。")

    try:
        probe = Image.open(BytesIO(data))
        probe.verify()
        image = Image.open(BytesIO(data))
        image_format = (image.format or "").upper()
        width, height = image.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise UploadError("无法识别该图片，仅支持 JPG/PNG/GIF/WEBP。") from exc

    if image_format not in current_app.config["ALLOWED_IMAGE_FORMATS"]:
        raise UploadError("仅支持 JPG、PNG、GIF、WEBP 格式的图片。")
    if width < 16 or height < 16:
        raise UploadError("图片尺寸过小，请上传正常图片。")
    if width * height > 40_000_000:
        raise UploadError("图片像素过大，请压缩到 4000 万像素以内。")

    ext_map = {"JPEG": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp"}
    ext = ext_map[image_format]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    now = datetime.now()
    relative_dir = Path("uploads") / f"{now:%Y}" / f"{now:%m}"
    target_dir = Path(current_app.config["UPLOAD_FOLDER"]) / f"{now:%Y}" / f"{now:%m}"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / stored_name).write_bytes(data)

    mime = Image.MIME.get(image_format, "application/octet-stream")
    safe_stem = secure_filename(Path(original_name).stem)[:50] or "image"
    return {
        "original_name": f"{safe_stem}{ext}" if not original_name else original_name,
        "stored_name": stored_name,
        "file_path": (relative_dir / stored_name).as_posix(),
        "mime_type": mime,
        "file_size": len(data),
        "width": width,
        "height": height,
    }


def delete_uploaded_file(relative_path: str) -> bool:
    """只允许删除 uploads 目录内的文件，防止路径穿越。"""
    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target = (Path(current_app.root_path) / "static" / relative_path).resolve()
    if upload_root not in target.parents:
        return False
    if target.is_file():
        target.unlink()
        return True
    return False


# ---------- 请求辅助 ----------


def visitor_key() -> str:
    """IP + UA + SECRET_KEY 的不可逆标识，不保存原始 IP。"""
    raw = "|".join(
        [
            request.headers.get("X-Forwarded-For", request.remote_addr or ""),
            request.headers.get("User-Agent", ""),
            current_app.config["SECRET_KEY"],
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_safe_url(target: str | None) -> bool:
    """仅允许站内跳转，避免开放重定向。"""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def is_valid_email(value: str) -> bool:
    if not value:
        return True
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def parse_hex_color(value: str, fallback: str = "#1f6f5c") -> str:
    value = (value or "").strip()
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback


def truncate(value: str, length: int) -> str:
    value = value or ""
    return value if len(value) <= length else value[: length - 1] + "…"
