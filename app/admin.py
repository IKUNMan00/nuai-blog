"""后台管理：数据看板、文章、分类、标签、评论审核、附件。

权限：只有 role=admin 的博主账号可以进入。
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import joinedload, selectinload

from .extensions import db
from .models import Attachment, Category, Comment, Favorite, Post, PostView, Tag, User
from .utils import (
    UploadError,
    delete_uploaded_file,
    is_safe_url,
    parse_hex_color,
    persist_image,
    render_markdown,
    summarize,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

POST_LOADS = (
    joinedload(Post.category),
    joinedload(Post.author),
    selectinload(Post.tags),
)


@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated:
        flash("请先使用博主账号登录后台。", "warning")
        return redirect(url_for("auth.login", next=request.url))
    if not current_user.is_admin:
        abort(403)
    # 侧边栏待审核角标，所有后台页面共用
    g.pending_comment_badge = db.session.scalar(
        select(func.count(Comment.id)).where(Comment.status == "pending")
    ) or 0
    return None


@admin_bp.route("/")
def index():
    return redirect(url_for("admin.dashboard"))


# ---------------------------------------------------------------- 数据看板
@admin_bp.route("/dashboard")
def dashboard():
    today_start = datetime.combine(date.today(), time.min)
    week_start = today_start - timedelta(days=6)

    total_posts = db.session.scalar(select(func.count(Post.id))) or 0
    published_count = db.session.scalar(
        select(func.count(Post.id)).where(Post.status == "published")
    ) or 0
    draft_count = total_posts - published_count
    total_views = db.session.scalar(
        select(func.coalesce(func.sum(Post.view_count), 0))
    ) or 0
    today_views = db.session.scalar(
        select(func.count(PostView.id)).where(PostView.viewed_at >= today_start)
    ) or 0
    week_views = db.session.scalar(
        select(func.count(PostView.id)).where(PostView.viewed_at >= week_start)
    ) or 0
    pending_comments = db.session.scalar(
        select(func.count(Comment.id)).where(Comment.status == "pending")
    ) or 0
    total_comments = db.session.scalar(select(func.count(Comment.id))) or 0
    total_favorites = db.session.scalar(select(func.count()).select_from(Favorite)) or 0
    reader_count = db.session.scalar(
        select(func.count(User.id)).where(User.role == "reader")
    ) or 0

    # 近 7 日趋势：在 Python 侧聚合，兼容 MySQL 与 SQLite
    recent_view_times = db.session.scalars(
        select(PostView.viewed_at).where(PostView.viewed_at >= week_start)
    ).all()
    day_counter = Counter(value.strftime("%Y-%m-%d") for value in recent_view_times if value)
    chart = []
    for offset in range(7):
        day = (week_start + timedelta(days=offset)).date()
        chart.append(
            {
                "label": f"{day.month}/{day.day}",
                "weekday": "一二三四五六日"[day.weekday()],
                "value": day_counter.get(day.strftime("%Y-%m-%d"), 0),
            }
        )
    max_value = max((item["value"] for item in chart), default=0)
    for item in chart:
        item["height"] = max(6, round(item["value"] / max_value * 100)) if max_value else 6

    category_rows = db.session.execute(
        select(Category, func.count(Post.id))
        .outerjoin(Post, and_(Post.category_id == Category.id, Post.status == "published"))
        .group_by(Category.id)
        .order_by(func.count(Post.id).desc())
    ).all()
    category_total = sum(count for _, count in category_rows) or 1
    category_chart = [
        {
            "name": category.name,
            "color": category.color,
            "count": count,
            "percent": round(count / category_total * 100),
        }
        for category, count in category_rows
    ]

    top_posts = db.session.scalars(
        select(Post)
        .where(Post.status == "published")
        .options(*POST_LOADS)
        .order_by(Post.view_count.desc(), Post.published_at.desc())
        .limit(5)
    ).unique().all()
    recent_posts = db.session.scalars(
        select(Post).options(*POST_LOADS).order_by(Post.updated_at.desc()).limit(5)
    ).unique().all()
    recent_comments = db.session.scalars(
        select(Comment)
        .options(joinedload(Comment.user), joinedload(Comment.post))
        .order_by(Comment.created_at.desc())
        .limit(5)
    ).all()

    return render_template(
        "admin/dashboard.html",
        total_posts=total_posts,
        published_count=published_count,
        draft_count=draft_count,
        total_views=total_views,
        today_views=today_views,
        week_views=week_views,
        pending_comments=pending_comments,
        total_comments=total_comments,
        total_favorites=total_favorites,
        reader_count=reader_count,
        chart=chart,
        chart_total=sum(item["value"] for item in chart),
        category_chart=category_chart,
        top_posts=top_posts,
        recent_posts=recent_posts,
        recent_comments=recent_comments,
    )


# ---------------------------------------------------------------- 文章管理
@admin_bp.route("/posts")
def posts():
    q = (request.args.get("q") or "").strip()[:80]
    status = request.args.get("status") or "all"
    page = max(1, request.args.get("page", 1, type=int))

    stmt = select(Post).options(*POST_LOADS)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Post.title.ilike(pattern), Post.summary.ilike(pattern)))
    if status in {"draft", "published"}:
        stmt = stmt.where(Post.status == status)
    stmt = stmt.order_by(Post.updated_at.desc(), Post.id.desc())

    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config["ADMIN_PAGE_SIZE"],
        error_out=False,
        max_per_page=50,
    )
    counts = {
        "all": db.session.scalar(select(func.count(Post.id))) or 0,
        "published": db.session.scalar(
            select(func.count(Post.id)).where(Post.status == "published")
        ) or 0,
        "draft": db.session.scalar(
            select(func.count(Post.id)).where(Post.status == "draft")
        ) or 0,
    }
    return render_template(
        "admin/posts.html",
        pagination=pagination,
        q=q,
        status=status,
        counts=counts,
    )


def _form_options() -> dict:
    categories = db.session.scalars(
        select(Category).order_by(Category.sort_order, Category.id)
    ).all()
    tags = db.session.scalars(select(Tag).order_by(Tag.name)).all()
    return {"categories": categories, "tags": tags}


def _form_data(post: Post | None = None) -> dict:
    if request.method == "POST":
        return request.form
    if post is None:
        return {"status": "draft"}
    return {
        "title": post.title,
        "summary": post.summary or "",
        "content_md": post.content_md,
        "cover_image": post.cover_image or "",
        "category_id": post.category_id,
        "status": post.status,
        "is_top": "on" if post.is_top else "",
        "tags": [str(tag.id) for tag in post.tags],
    }


def _selected_tag_ids() -> set[int]:
    if request.method == "POST":
        result = set()
        for raw in request.form.getlist("tags"):
            try:
                result.add(int(raw))
            except (TypeError, ValueError):
                continue
        return result
    return set()


def _validate_post_form() -> tuple[dict, list[str]]:
    title = (request.form.get("title") or "").strip()
    summary = (request.form.get("summary") or "").strip()
    content_md = (request.form.get("content_md") or "").strip()
    cover_image = (request.form.get("cover_image") or "").strip()
    category_raw = request.form.get("category_id") or ""
    action = request.form.get("action") or "draft"

    errors: list[str] = []
    if not 2 <= len(title) <= 150:
        errors.append("标题需为 2–150 个字符。")
    if len(summary) > 300:
        errors.append("摘要不能超过 300 个字符。")
    if len(content_md) < 10:
        errors.append("正文至少需要 10 个字符。")
    if len(content_md) > 200_000:
        errors.append("正文过长，请控制在 20 万字符以内。")

    category_id = None
    if category_raw:
        try:
            category_id = int(category_raw)
        except ValueError:
            errors.append("分类参数不合法。")
        else:
            if not db.session.get(Category, category_id):
                errors.append("所选分类不存在。")

    if cover_image and not (
        cover_image.startswith("https://")
        or cover_image.startswith("http://")
        or cover_image.startswith("/static/")
    ):
        errors.append("封面地址需为 http(s) 链接或站内 /static/ 路径。")

    tag_ids: list[int] = []
    for raw in request.form.getlist("tags"):
        try:
            tag_ids.append(int(raw))
        except (TypeError, ValueError):
            continue
    valid_tag_ids = set(
        db.session.scalars(select(Tag.id).where(Tag.id.in_(tag_ids))).all()
    ) if tag_ids else set()
    if len(valid_tag_ids) != len(set(tag_ids)):
        errors.append("部分标签不存在，请刷新后重试。")

    raw_new_tags = (request.form.get("new_tags") or "").replace("，", ",")
    new_tags = []
    for item in raw_new_tags.split(","):
        name = item.strip().lstrip("#")
        if not name:
            continue
        if len(name) > 20:
            errors.append("新标签名称不能超过 20 个字符。")
            break
        if name not in new_tags:
            new_tags.append(name)
    if len(new_tags) > 5:
        errors.append("一次最多新建 5 个标签。")

    data = {
        "title": title,
        "summary": summary or summarize(content_md, 110),
        "content_md": content_md,
        "cover_image": cover_image or None,
        "category_id": category_id,
        "status": "published" if action == "publish" else "draft",
        "is_top": request.form.get("is_top") == "on",
        "tag_ids": valid_tag_ids,
        "new_tags": new_tags,
    }
    return data, errors


def _sync_tags(post: Post, data: dict) -> None:
    tags = []
    if data["tag_ids"]:
        tags = list(
            db.session.scalars(select(Tag).where(Tag.id.in_(data["tag_ids"]))).all()
        )
    existing_names = {tag.name.lower() for tag in tags}
    palette = ["#1f6f5c", "#c96f3b", "#3b6ea8", "#8b5cf6", "#b45309", "#0f766e"]
    for index, name in enumerate(data["new_tags"]):
        if name.lower() in existing_names:
            continue
        tag = db.session.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()))
        if not tag:
            tag = Tag(name=name, color=palette[(len(tags) + index) % len(palette)])
            db.session.add(tag)
            db.session.flush()
        tags.append(tag)
        existing_names.add(name.lower())
    post.tags = tags


def _save_cover_if_any(data: dict) -> Attachment | None:
    file = request.files.get("cover_file")
    if not file or not file.filename:
        return None
    meta = persist_image(file)
    attachment = Attachment(
        user_id=current_user.id,
        original_name=meta["original_name"],
        stored_name=meta["stored_name"],
        file_path=meta["file_path"],
        mime_type=meta["mime_type"],
        file_size=meta["file_size"],
    )
    db.session.add(attachment)
    data["cover_image"] = f"/static/{meta['file_path']}"
    return attachment


@admin_bp.route("/posts/new", methods=["GET", "POST"])
def post_new():
    post = None
    options = _form_options()
    selected_tag_ids: set[int] = set()

    if request.method == "POST":
        data, errors = _validate_post_form()
        selected_tag_ids = {int(value) for value in data["tag_ids"]}
        if not errors:
            try:
                _save_cover_if_any(data)
            except UploadError as exc:
                errors.append(str(exc))
        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template(
                "admin/post_form.html",
                post=None,
                form=_form_data(),
                selected_tag_ids=selected_tag_ids,
                **options,
            )

        post = Post(
            title=data["title"],
            summary=data["summary"],
            content_md=data["content_md"],
            content_html=render_markdown(data["content_md"]),
            cover_image=data["cover_image"],
            category_id=data["category_id"],
            author_id=current_user.id,
            status=data["status"],
            is_top=data["is_top"],
            published_at=datetime.now() if data["status"] == "published" else None,
        )
        db.session.add(post)
        db.session.flush()
        _sync_tags(post, data)
        db.session.commit()
        flash("文章已创建。" if post.status == "published" else "草稿已保存。", "success")
        return redirect(url_for("admin.posts"))

    return render_template(
        "admin/post_form.html",
        post=post,
        form=_form_data(post),
        selected_tag_ids=selected_tag_ids,
        **options,
    )


@admin_bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
def post_edit(post_id: int):
    post = db.session.scalar(select(Post).options(*POST_LOADS).where(Post.id == post_id))
    if not post:
        abort(404)

    options = _form_options()
    selected_tag_ids = {tag.id for tag in post.tags}

    if request.method == "POST":
        data, errors = _validate_post_form()
        selected_tag_ids = {int(value) for value in data["tag_ids"]}
        if not errors:
            try:
                _save_cover_if_any(data)
            except UploadError as exc:
                errors.append(str(exc))
        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template(
                "admin/post_form.html",
                post=post,
                form=_form_data(post),
                selected_tag_ids=selected_tag_ids,
                **options,
            )

        was_published = post.status == "published"
        post.title = data["title"]
        post.summary = data["summary"]
        post.content_md = data["content_md"]
        post.content_html = render_markdown(data["content_md"])
        post.cover_image = data["cover_image"]
        post.category_id = data["category_id"]
        post.status = data["status"]
        post.is_top = data["is_top"]
        if post.status == "published" and (not was_published or not post.published_at):
            post.published_at = datetime.now()
        if post.status == "draft":
            post.published_at = None
        _sync_tags(post, data)
        db.session.commit()
        flash("文章已更新。" if post.status == "published" else "已转为草稿。", "success")
        return redirect(url_for("admin.posts"))

    return render_template(
        "admin/post_form.html",
        post=post,
        form=_form_data(post),
        selected_tag_ids=selected_tag_ids,
        **options,
    )


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
def post_delete(post_id: int):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    title = post.title
    db.session.delete(post)
    db.session.commit()
    flash(f"文章《{title}》已删除。", "success")
    return redirect(url_for("admin.posts"))


# ---------------------------------------------------------------- 分类管理
def _validate_taxonomy(name_label: str = "名称") -> tuple[dict, list[str]]:
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()
    color = parse_hex_color(request.form.get("color") or "", "#1f6f5c")
    sort_order = request.form.get("sort_order", type=int) or 0
    errors = []
    if not 1 <= len(name) <= 50:
        errors.append(f"{name_label}长度需为 1–50 个字符。")
    if len(description) > 255:
        errors.append("说明不能超过 255 个字符。")
    return {
        "name": name,
        "description": description,
        "color": color,
        "sort_order": max(-999, min(999, sort_order)),
    }, errors


@admin_bp.route("/categories", methods=["GET", "POST"])
def categories():
    if request.method == "POST":
        data, errors = _validate_taxonomy("分类名称")
        if db.session.scalar(
            select(Category).where(func.lower(Category.name) == data["name"].lower())
        ):
            errors.append("该分类已存在。")
        if errors:
            for message in errors:
                flash(message, "danger")
        else:
            db.session.add(Category(**data))
            db.session.commit()
            flash("分类已添加。", "success")
        return redirect(url_for("admin.categories"))

    rows = db.session.execute(
        select(Category, func.count(Post.id))
        .outerjoin(Post, Post.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.sort_order, Category.id)
    ).all()
    return render_template("admin/categories.html", rows=rows)


@admin_bp.route("/categories/<int:category_id>/edit", methods=["POST"])
def category_edit(category_id: int):
    category = db.session.get(Category, category_id)
    if not category:
        abort(404)
    data, errors = _validate_taxonomy("分类名称")
    duplicate = db.session.scalar(
        select(Category).where(
            func.lower(Category.name) == data["name"].lower(),
            Category.id != category.id,
        )
    )
    if duplicate:
        errors.append("该分类名称已存在。")
    if errors:
        for message in errors:
            flash(message, "danger")
        return redirect(url_for("admin.categories"))
    for key, value in data.items():
        setattr(category, key, value)
    db.session.commit()
    flash("分类已更新。", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
def category_delete(category_id: int):
    category = db.session.get(Category, category_id)
    if not category:
        abort(404)
    count = db.session.scalar(
        select(func.count(Post.id)).where(Post.category_id == category.id)
    ) or 0
    db.session.execute(
        update(Post).where(Post.category_id == category.id).values(category_id=None)
    )
    db.session.delete(category)
    db.session.commit()
    flash(f"分类已删除，{count} 篇文章已归入未分类。", "success")
    return redirect(url_for("admin.categories"))


# ---------------------------------------------------------------- 标签管理
@admin_bp.route("/tags", methods=["GET", "POST"])
def tags():
    if request.method == "POST":
        data, errors = _validate_taxonomy("标签名称")
        data.pop("description", None)
        data.pop("sort_order", None)
        if db.session.scalar(
            select(Tag).where(func.lower(Tag.name) == data["name"].lower())
        ):
            errors.append("该标签已存在。")
        if errors:
            for message in errors:
                flash(message, "danger")
        else:
            db.session.add(Tag(**data))
            db.session.commit()
            flash("标签已添加。", "success")
        return redirect(url_for("admin.tags"))

    rows = db.session.execute(
        select(Tag, func.count(Post.id))
        .outerjoin(Tag.posts)
        .group_by(Tag.id)
        .order_by(func.count(Post.id).desc(), Tag.name)
    ).all()
    return render_template("admin/tags.html", rows=rows)


@admin_bp.route("/tags/<int:tag_id>/edit", methods=["POST"])
def tag_edit(tag_id: int):
    tag = db.session.get(Tag, tag_id)
    if not tag:
        abort(404)
    data, errors = _validate_taxonomy("标签名称")
    data.pop("description", None)
    data.pop("sort_order", None)
    duplicate = db.session.scalar(
        select(Tag).where(func.lower(Tag.name) == data["name"].lower(), Tag.id != tag.id)
    )
    if duplicate:
        errors.append("该标签名称已存在。")
    if errors:
        for message in errors:
            flash(message, "danger")
        return redirect(url_for("admin.tags"))
    tag.name = data["name"]
    tag.color = data["color"]
    db.session.commit()
    flash("标签已更新。", "success")
    return redirect(url_for("admin.tags"))


@admin_bp.route("/tags/<int:tag_id>/delete", methods=["POST"])
def tag_delete(tag_id: int):
    tag = db.session.get(Tag, tag_id)
    if not tag:
        abort(404)
    db.session.delete(tag)
    db.session.commit()
    flash("标签已删除，相关文章的其他标签不受影响。", "success")
    return redirect(url_for("admin.tags"))


# ---------------------------------------------------------------- 评论审核
@admin_bp.route("/comments")
def comments():
    status = request.args.get("status") or "pending"
    if status not in {"pending", "approved", "rejected", "all"}:
        status = "pending"
    page = max(1, request.args.get("page", 1, type=int))

    stmt = select(Comment).options(
        joinedload(Comment.user), joinedload(Comment.post)
    )
    if status != "all":
        stmt = stmt.where(Comment.status == status)
    stmt = stmt.order_by(
        Comment.created_at.desc(), Comment.id.desc()
    )
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config["ADMIN_PAGE_SIZE"],
        error_out=False,
        max_per_page=50,
    )
    counts = {
        key: db.session.scalar(
            select(func.count(Comment.id)).where(Comment.status == key)
        ) or 0
        for key in ("pending", "approved", "rejected")
    }
    counts["all"] = sum(counts.values())
    return render_template(
        "admin/comments.html",
        pagination=pagination,
        status=status,
        counts=counts,
    )


@admin_bp.route("/comments/<int:comment_id>/<action>", methods=["POST"])
def comment_action(comment_id: int, action: str):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        abort(404)
    if action == "approve":
        comment.status = "approved"
        comment.audited_at = datetime.now()
        comment.audited_by = current_user.id
        flash("评论已通过审核。", "success")
    elif action == "reject":
        comment.status = "rejected"
        comment.audited_at = datetime.now()
        comment.audited_by = current_user.id
        flash("评论已驳回。", "info")
    elif action == "delete":
        db.session.delete(comment)
        flash("评论已删除。", "success")
    else:
        abort(400)
    db.session.commit()
    next_url = request.form.get("next")
    if is_safe_url(next_url):
        return redirect(next_url)
    return redirect(url_for("admin.comments", status=request.form.get("status", "pending")))


# ---------------------------------------------------------------- 附件管理
@admin_bp.route("/attachments")
def attachments():
    page = max(1, request.args.get("page", 1, type=int))
    stmt = (
        select(Attachment)
        .options(joinedload(Attachment.user))
        .order_by(Attachment.created_at.desc())
    )
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=12,
        error_out=False,
        max_per_page=48,
    )
    total_size = db.session.scalar(
        select(func.coalesce(func.sum(Attachment.file_size), 0))
    ) or 0
    return render_template(
        "admin/attachments.html", pagination=pagination, total_size=total_size
    )


@admin_bp.route("/attachments/upload", methods=["POST"])
def attachment_upload():
    try:
        meta = persist_image(request.files.get("file"))
    except UploadError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.attachments"))
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
    flash("图片上传成功，可复制 Markdown 链接插入文章。", "success")
    return redirect(url_for("admin.attachments"))


@admin_bp.route("/attachments/<int:attachment_id>/delete", methods=["POST"])
def attachment_delete(attachment_id: int):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        abort(404)
    delete_uploaded_file(attachment.file_path)
    db.session.delete(attachment)
    db.session.commit()
    flash("附件记录与文件已删除。", "success")
    return redirect(url_for("admin.attachments"))
