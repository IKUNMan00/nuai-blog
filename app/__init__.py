"""应用工厂：注册扩展、蓝图、模板过滤器、错误页和 CLI 命令。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, url_for
from flask_wtf.csrf import CSRFError

from config import Config
from .extensions import csrf, db, login_manager


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "请先登录后再进行该操作。"
    login_manager.login_message_category = "warning"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    # ---------- 蓝图 ----------
    from .auth import auth_bp
    from .main import main_bp
    from .account import account_bp
    from .admin import admin_bp
    from .api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # ---------- 模板过滤器 ----------
    @app.template_filter("datetime_cn")
    def datetime_cn(value: datetime | None, fmt: str = "%Y年%m月%d日") -> str:
        if not value:
            return "—"
        return value.strftime(fmt)

    @app.template_filter("date_short")
    def date_short(value: datetime | None) -> str:
        return value.strftime("%m.%d") if value else "—"

    @app.template_filter("number_cn")
    def number_cn(value) -> str:
        try:
            number = int(value or 0)
        except (TypeError, ValueError):
            return "0"
        if number >= 10000:
            return f"{number / 10000:.1f}w"
        if number >= 1000:
            return f"{number / 1000:.1f}k"
        return str(number)

    @app.template_filter("initials")
    def initials(value) -> str:
        text = (value or "?").strip()
        return text[0].upper() if text else "?"

    # ---------- 模板全局变量 ----------
    @app.context_processor
    def inject_globals():
        def page_url(page: int) -> str:
            args = request.args.to_dict(flat=True)
            args["page"] = page
            return url_for(request.endpoint or "main.index", **args)

        def filter_url(endpoint: str = "main.posts", **updates) -> str:
            """生成保留现有查询参数的链接，None/空字符串表示移除该参数。"""
            args = request.args.to_dict(flat=True)
            args.pop("page", None)
            for key, value in updates.items():
                if value in (None, ""):
                    args.pop(key, None)
                else:
                    args[key] = value
            return url_for(endpoint, **args)

        return {
            "site_name": app.config["SITE_NAME"],
            "site_subtitle": app.config["SITE_SUBTITLE"],
            "site_description": app.config["SITE_DESCRIPTION"],
            "site_author": app.config["SITE_AUTHOR"],
            "current_year": datetime.now().year,
            "page_url": page_url,
            "filter_url": filter_url,
        }

    # ---------- 安全响应头 ----------
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        return response

    # ---------- 错误处理 ----------
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "message": "文件过大，单次请求不能超过 8MB。"}), 413
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "message": "页面令牌已过期，请刷新后重试。"}), 400
        return render_template("errors/400.html", message="表单令牌已过期，请返回刷新后重试。"), 400

    # ---------- CLI ----------
    from .cli import register_commands

    register_commands(app)
    return app
