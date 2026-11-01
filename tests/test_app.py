"""课程项目核心功能测试：页面、权限、CRUD、搜索、评论、收藏、上传。"""
from __future__ import annotations

from io import BytesIO

from PIL import Image
from sqlalchemy import select

from app.extensions import db
from app.models import Attachment, Comment, Favorite, Post, Tag
from app.utils import render_markdown


def test_home_and_public_pages(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "我的知识小栈" in response.get_data(as_text=True)
    assert "Flask 测试文章" in response.get_data(as_text=True)

    for path in ["/posts", "/posts/1", "/about", "/auth/login", "/auth/register"]:
        assert client.get(path).status_code == 200, path


def test_login_and_admin_dashboard(client, login_admin):
    response = login_admin()
    assert response.status_code == 200
    assert "数据看板" in response.get_data(as_text=True)
    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200
    assert "访问趋势" in dashboard.get_data(as_text=True)


def test_reader_cannot_access_admin(client, login_reader):
    login_reader()
    response = client.get("/admin/dashboard")
    assert response.status_code == 403
    assert "没有访问权限" in response.get_data(as_text=True)


def test_create_edit_and_delete_post(client, login_admin, app):
    login_admin()
    response = client.post(
        "/admin/posts/new",
        data={
            "title": "新发布的测试文章",
            "summary": "这是新文章的摘要",
            "content_md": "## 小标题\n\n这是新文章正文，包含 MySQL 和 Flask。",
            "category_id": str(app.config["TEST_IDS"]["category"]),
            "tags": [str(app.config["TEST_IDS"]["tag"])],
            "new_tags": "项目复盘, 测试标签",
            "action": "publish",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "文章已创建" in response.get_data(as_text=True)

    with app.app_context():
        post = db.session.scalar(select(Post).where(Post.title == "新发布的测试文章"))
        assert post is not None
        assert post.status == "published"
        assert {tag.name for tag in post.tags} >= {"Flask", "项目复盘", "测试标签"}
        post_id = post.id

    edit = client.post(
        f"/admin/posts/{post_id}/edit",
        data={
            "title": "修改后的测试文章",
            "summary": "修改后的摘要",
            "content_md": "修改后的正文内容，至少十个字符。",
            "action": "draft",
        },
        follow_redirects=True,
    )
    assert edit.status_code == 200
    with app.app_context():
        post = db.session.get(Post, post_id)
        assert post.title == "修改后的测试文章"
        assert post.status == "draft"
        assert post.published_at is None

    delete = client.post(f"/admin/posts/{post_id}/delete", follow_redirects=True)
    assert delete.status_code == 200
    with app.app_context():
        assert db.session.get(Post, post_id) is None


def test_search_matches_title_and_content(client, app):
    response = client.get("/posts?q=Flask")
    assert response.status_code == 200
    assert "Flask 测试文章" in response.get_data(as_text=True)

    response = client.get("/search?q=搜索关键词")
    assert response.status_code == 302
    follow = client.get(response.headers["Location"])
    assert "Flask 测试文章" in follow.get_data(as_text=True)

    response = client.get("/posts?q=不存在的关键词")
    assert "没有找到匹配的笔记" in response.get_data(as_text=True)


def test_guest_comment_requires_audit(client, login_admin, app):
    post_id = app.config["TEST_IDS"]["post"]
    response = client.post(
        f"/posts/{post_id}/comments",
        data={"guest_name": "新访客", "guest_email": "new@example.com", "content": "这是一条新的测试评论。"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "评论已提交" in response.get_data(as_text=True)

    with app.app_context():
        comment = db.session.scalar(
            select(Comment).where(Comment.content == "这是一条新的测试评论。")
        )
        assert comment is not None
        assert comment.status == "pending"
        comment_id = comment.id

    # 待审核评论不对公众展示
    assert "这是一条新的测试评论。" not in client.get(f"/posts/{post_id}").get_data(as_text=True)

    login_admin()
    approve = client.post(
        f"/admin/comments/{comment_id}/approve",
        data={"status": "pending"},
        follow_redirects=True,
    )
    assert approve.status_code == 200
    with app.app_context():
        assert db.session.get(Comment, comment_id).status == "approved"
    assert "这是一条新的测试评论。" in client.get(f"/posts/{post_id}").get_data(as_text=True)


def test_favorite_toggle(client, login_reader, app):
    login_reader()
    post_id = app.config["TEST_IDS"]["post"]
    response = client.post(f"/posts/{post_id}/favorite", follow_redirects=True)
    assert response.status_code == 200
    assert "已收藏" in response.get_data(as_text=True)

    with app.app_context():
        favorite = db.session.scalar(
            select(Favorite).where(
                Favorite.user_id == app.config["TEST_IDS"]["reader"],
                Favorite.post_id == post_id,
            )
        )
        assert favorite is not None

    response = client.post(f"/posts/{post_id}/favorite", follow_redirects=True)
    assert "已取消收藏" in response.get_data(as_text=True)
    with app.app_context():
        assert (
            db.session.scalar(
                select(Favorite).where(
                    Favorite.user_id == app.config["TEST_IDS"]["reader"],
                    Favorite.post_id == post_id,
                )
            )
            is None
        )


def test_register_creates_reader(client, app):
    response = client.post(
        "/auth/register",
        data={
            "username": "new_reader",
            "email": "new_reader@example.com",
            "display_name": "新读者",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "注册成功" in response.get_data(as_text=True)
    with app.app_context():
        from app.models import User

        user = db.session.scalar(select(User).where(User.username == "new_reader"))
        assert user is not None
        assert user.role == "reader"


def test_markdown_is_sanitized():
    html = render_markdown('<script>alert("xss")</script>\n\n**安全内容**')
    assert "<script" not in html
    assert "安全内容" in html
    markdown_html = render_markdown("[链接](javascript:alert(1))")
    assert "javascript:" not in markdown_html


def test_image_upload_validation_and_success(client, login_admin, app):
    login_admin()
    bad = client.post(
        "/api/upload",
        data={"file": (BytesIO(b"not an image"), "bad.txt")},
        content_type="multipart/form-data",
    )
    assert bad.status_code == 400
    assert bad.get_json()["ok"] is False

    image_buffer = BytesIO()
    Image.new("RGB", (32, 32), (31, 111, 92)).save(image_buffer, "PNG")
    image_buffer.seek(0)
    good = client.post(
        "/api/upload",
        data={"file": (image_buffer, "cover.png")},
        content_type="multipart/form-data",
    )
    assert good.status_code == 200
    payload = good.get_json()
    assert payload["ok"] is True
    assert payload["url"].startswith("/static/uploads/")
    with app.app_context():
        assert db.session.scalar(select(Attachment)) is not None


def test_admin_smoke_pages(client, login_admin, app):
    login_admin()
    paths = [
        "/admin/",
        "/admin/dashboard",
        "/admin/posts",
        "/admin/posts/new",
        f"/admin/posts/{app.config['TEST_IDS']['post']}/edit",
        "/admin/categories",
        "/admin/tags",
        "/admin/comments",
        "/admin/comments?status=all",
        "/admin/attachments",
        "/account",
        "/account/favorites",
        "/account/comments",
    ]
    for path in paths:
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200, f"{path} -> {response.status_code}"


def test_account_redirects_for_guest(client):
    for path in ["/account", "/account/favorites", "/admin/dashboard"]:
        response = client.get(path)
        assert response.status_code == 302, path


def test_tag_and_category_management(client, login_admin, app):
    login_admin()
    response = client.post(
        "/admin/categories",
        data={"name": "新分类", "description": "测试新分类", "color": "#123456", "sort_order": "9"},
        follow_redirects=True,
    )
    assert "分类已添加" in response.get_data(as_text=True)

    response = client.post(
        "/admin/tags",
        data={"name": "新标签", "color": "#abcdef"},
        follow_redirects=True,
    )
    assert "标签已添加" in response.get_data(as_text=True)

    with app.app_context():
        assert db.session.scalar(select(Tag).where(Tag.name == "新标签")) is not None
