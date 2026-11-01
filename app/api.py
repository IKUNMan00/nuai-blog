"""轻量 JSON 接口：Markdown 实时预览、编辑器图片上传。"""
from __future__ import annotations

from flask import Blueprint, jsonify, request, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import Attachment
from .utils import UploadError, persist_image, render_markdown

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.before_request
@login_required
def require_login():
    return None


@api_bp.route("/markdown/preview", methods=["POST"])
def markdown_preview():
    if not current_user.is_admin:
        return jsonify({"ok": False, "message": "只有博主账号可以使用编辑器。"}), 403
    payload = request.get_json(silent=True) or {}
    content = payload.get("content") or ""
    if not isinstance(content, str):
        return jsonify({"ok": False, "message": "内容格式不正确。"}), 400
    if len(content) > 200_000:
        return jsonify({"ok": False, "message": "内容过长，无法预览。"}), 413
    return jsonify(
        {
            "ok": True,
            "html": render_markdown(content),
            "characters": len(content),
        }
    )


@api_bp.route("/upload", methods=["POST"])
def upload_image():
    if not current_user.is_admin:
        return jsonify({"ok": False, "message": "只有博主账号可以上传图片。"}), 403
    try:
        meta = persist_image(request.files.get("file"))
    except UploadError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

    attachment = Attachment(
        user_id=current_user.id,
        original_name=meta["original_name"],
        stored_name=meta["stored_name"],
        file_path=meta["file_path"],
        mime_type=meta["mime_type"],
        file_size=meta["file_size"],
    )
    db.session.add(attachment)
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "url": url_for("static", filename=meta["file_path"]),
            "markdown": f"![{meta['original_name']}]({url_for('static', filename=meta['file_path'])})",
            "name": meta["original_name"],
            "size": meta["file_size"],
        }
    )
