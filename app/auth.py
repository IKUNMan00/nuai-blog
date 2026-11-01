"""认证模块：登录、注册、退出。

角色规则：
- admin：博主本人 / 站点管理员，由 CLI 创建或由管理员提升；
- reader：公开注册的读者，可收藏、评论，不能进入后台。
"""
from __future__ import annotations

import re
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from .extensions import db
from .models import User
from .utils import is_safe_url

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
PASSWORD_MIN = 8


def _redirect_after_login() -> str:
    next_url = request.args.get("next") or request.form.get("next")
    if is_safe_url(next_url):
        return next_url
    return url_for("admin.dashboard") if current_user.is_admin else url_for("main.index")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "on"

        if not identifier or not password:
            flash("请输入用户名/邮箱和密码。", "danger")
            return render_template("auth/login.html", identifier=identifier), 400

        user = db.session.scalar(
            db.select(User).where(
                or_(User.username == identifier, User.email == identifier.lower())
            )
        )
        if not user or not user.check_password(password):
            # 统一提示，避免暴露账号是否存在
            flash("用户名/邮箱或密码不正确，请重新输入。", "danger")
            return render_template("auth/login.html", identifier=identifier), 400
        if not user.is_active:
            flash("该账号已被停用，请联系博主。", "danger")
            return render_template("auth/login.html", identifier=identifier), 403

        login_user(user, remember=remember)
        user.last_login_at = datetime.now()
        db.session.commit()
        flash(f"欢迎回来，{user.display_name}。", "success")
        return redirect(_redirect_after_login())

    return render_template("auth/login.html", identifier="")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = {
        "username": "",
        "email": "",
        "display_name": "",
    }

    if request.method == "POST":
        form = {
            "username": (request.form.get("username") or "").strip(),
            "email": (request.form.get("email") or "").strip().lower(),
            "display_name": (request.form.get("display_name") or "").strip(),
        }
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        errors: list[str] = []

        if not USERNAME_RE.fullmatch(form["username"]):
            errors.append("用户名需为 3–20 位字母、数字或下划线。")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", form["email"]):
            errors.append("请输入有效的邮箱地址。")
        if not 2 <= len(form["display_name"]) <= 20:
            errors.append("昵称长度需为 2–20 个字符。")
        if len(password) < PASSWORD_MIN:
            errors.append("密码至少 8 位。")
        if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
            errors.append("密码需同时包含字母和数字。")
        if password != confirm:
            errors.append("两次输入的密码不一致。")

        if db.session.scalar(
            db.select(User).where(
                or_(User.username == form["username"], User.email == form["email"])
            )
        ):
            errors.append("用户名或邮箱已被注册，请更换。")

        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template("auth/register.html", form=form), 400

        user = User(
            username=form["username"],
            email=form["email"],
            display_name=form["display_name"],
            role="reader",
            bio="刚刚加入知识小栈的读者。",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("注册成功，已自动登录。读者账号可以收藏文章、参与评论。", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("已安全退出登录。", "info")
    return redirect(url_for("main.index"))
