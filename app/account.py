"""读者 / 博主共用账号中心：资料、密码、收藏、评论记录。"""
from __future__ import annotations

import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from .extensions import db
from .models import Comment, Favorite, Post, User

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.before_request
@login_required
def require_login():
    """整个账号中心均要求登录。"""
    return None


@account_bp.route("", strict_slashes=False)
@account_bp.route("/", strict_slashes=False)
def overview():
    favorite_count = db.session.scalar(
        select(func.count()).select_from(Favorite).where(Favorite.user_id == current_user.id)
    ) or 0
    comment_count = db.session.scalar(
        select(func.count()).select_from(Comment).where(Comment.user_id == current_user.id)
    ) or 0
    return render_template(
        "account/overview.html",
        favorite_count=favorite_count,
        comment_count=comment_count,
    )


@account_bp.route("/profile", methods=["POST"])
def update_profile():
    display_name = (request.form.get("display_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    bio = (request.form.get("bio") or "").strip()
    avatar = (request.form.get("avatar") or "").strip()

    errors = []
    if not 2 <= len(display_name) <= 20:
        errors.append("昵称长度需为 2–20 个字符。")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("请输入有效的邮箱地址。")
    if len(bio) > 255:
        errors.append("个人简介不能超过 255 个字符。")
    if avatar and not (
        avatar.startswith("https://")
        or avatar.startswith("http://")
        or avatar.startswith("/static/")
    ):
        errors.append("头像地址需为 http(s) 链接或站内 /static/ 路径。")

    exists = db.session.scalar(
        select(User).where(User.email == email, User.id != current_user.id)
    )
    if exists:
        errors.append("该邮箱已被其他账号使用。")

    if errors:
        for message in errors:
            flash(message, "danger")
        return redirect(url_for("account.overview"))

    current_user.display_name = display_name
    current_user.email = email
    current_user.bio = bio
    current_user.avatar = avatar or None
    db.session.commit()
    flash("个人资料已更新。", "success")
    return redirect(url_for("account.overview"))


@account_bp.route("/password", methods=["POST"])
def change_password():
    old_password = request.form.get("old_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm = request.form.get("confirm_password") or ""

    errors = []
    if not current_user.check_password(old_password):
        errors.append("当前密码不正确。")
    if len(new_password) < 8:
        errors.append("新密码至少 8 位。")
    if not (re.search(r"[A-Za-z]", new_password) and re.search(r"\d", new_password)):
        errors.append("新密码需同时包含字母和数字。")
    if new_password != confirm:
        errors.append("两次输入的新密码不一致。")

    if errors:
        for message in errors:
            flash(message, "danger")
        return redirect(url_for("account.overview"))

    current_user.set_password(new_password)
    db.session.commit()
    flash("密码修改成功，下次请使用新密码登录。", "success")
    return redirect(url_for("account.overview"))


@account_bp.route("/favorites")
def favorites():
    page = max(1, request.args.get("page", 1, type=int))
    stmt = (
        select(Favorite)
        .join(Post, Favorite.post_id == Post.id)
        .where(Favorite.user_id == current_user.id, Post.status == "published")
        .options(
            joinedload(Favorite.post).joinedload(Post.category),
            joinedload(Favorite.post).joinedload(Post.author),
            joinedload(Favorite.post),
        )
        .order_by(Favorite.created_at.desc())
    )
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config["POSTS_PER_PAGE"],
        error_out=False,
        max_per_page=50,
    )
    return render_template("account/favorites.html", pagination=pagination)


@account_bp.route("/comments")
def comments():
    page = max(1, request.args.get("page", 1, type=int))
    stmt = (
        select(Comment)
        .where(Comment.user_id == current_user.id)
        .options(joinedload(Comment.post))
        .order_by(Comment.created_at.desc())
    )
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config["COMMENTS_PER_PAGE"],
        error_out=False,
        max_per_page=50,
    )
    return render_template("account/comments.html", pagination=pagination)
