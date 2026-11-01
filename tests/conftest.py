"""pytest 公共夹具：独立 SQLite 数据库 + 管理员/读者/示例文章。"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app import create_app
from app.extensions import db
from app.models import Category, Comment, Favorite, Post, Tag, User
from app.utils import render_markdown


@pytest.fixture()
def app(tmp_path: Path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "SQLALCHEMY_ENGINE_OPTIONS": {},
            "UPLOAD_FOLDER": str(upload_dir),
            "MAX_IMAGE_SIZE": 2 * 1024 * 1024,
        }
    )

    with app.app_context():
        db.create_all()

        admin = User(
            username="admin",
            email="admin@test.com",
            display_name="测试博主",
            role="admin",
            bio="测试用博主",
        )
        admin.set_password("Admin@123")
        reader = User(
            username="reader",
            email="reader@test.com",
            display_name="测试读者",
            role="reader",
        )
        reader.set_password("Reader@123")
        db.session.add_all([admin, reader])
        db.session.flush()

        category = Category(name="后端", color="#1f6f5c", sort_order=1)
        tag = Tag(name="Flask", color="#1f6f5c")
        db.session.add_all([category, tag])
        db.session.flush()

        content = "# 测试标题\n\n这是一篇用于测试的 **Flask** 文章，包含搜索关键词。\n\n```python\nprint('hello')\n```"
        post = Post(
            title="Flask 测试文章",
            summary="用于测试的文章摘要",
            content_md=content,
            content_html=render_markdown(content),
            category_id=category.id,
            author_id=admin.id,
            status="published",
            is_top=True,
            view_count=10,
            published_at=datetime.now() - timedelta(days=1),
        )
        post.tags = [tag]
        draft = Post(
            title="测试草稿",
            summary="草稿摘要",
            content_md="这是一篇还没有发布的草稿内容。",
            content_html=render_markdown("这是一篇还没有发布的草稿内容。"),
            author_id=admin.id,
            status="draft",
        )
        db.session.add_all([post, draft])
        db.session.flush()

        pending = Comment(
            post_id=post.id,
            guest_name="待审核访客",
            content="这是一条待审核的评论。",
            status="pending",
        )
        approved = Comment(
            post_id=post.id,
            user_id=reader.id,
            content="这是一条已通过的评论。",
            status="approved",
        )
        db.session.add_all([pending, approved])
        db.session.commit()

        app.config["TEST_IDS"] = {
            "admin": admin.id,
            "reader": reader.id,
            "category": category.id,
            "tag": tag.id,
            "post": post.id,
            "draft": draft.id,
            "pending_comment": pending.id,
        }

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def login_admin(client):
    def _login():
        return client.post(
            "/auth/login",
            data={"identifier": "admin", "password": "Admin@123"},
            follow_redirects=True,
        )

    return _login


@pytest.fixture()
def login_reader(client):
    def _login():
        return client.post(
            "/auth/login",
            data={"identifier": "reader", "password": "Reader@123"},
            follow_redirects=True,
        )

    return _login
