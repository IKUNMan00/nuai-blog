"""公开站点：首页、文章列表、搜索、详情、评论、收藏。"""
from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from .extensions import db
from .models import Category, Comment, Favorite, Post, PostView, Tag, User
from .utils import (
    is_safe_url,
    is_valid_email,
    visitor_key,
)

main_bp = Blueprint("main", __name__)

POST_LOADS = (
    joinedload(Post.category),
    joinedload(Post.author),
    selectinload(Post.tags),
)


def _published_posts():
    """所有公开文章查询的统一起点。"""
    return (
        select(Post)
        .where(Post.status == "published")
        .options(*POST_LOADS)
    )


def _site_stats() -> dict:
    published = db.session.scalar(
        select(func.count(Post.id)).where(Post.status == "published")
    ) or 0
    views = db.session.scalar(
        select(func.coalesce(func.sum(Post.view_count), 0)).where(Post.status == "published")
    ) or 0
    comments = db.session.scalar(
        select(func.count(Comment.id)).where(Comment.status == "approved")
    ) or 0
    favorites = db.session.scalar(select(func.count()).select_from(Favorite)) or 0
    return {
        "posts": published,
        "views": int(views),
        "comments": comments,
        "favorites": favorites,
    }


@main_bp.route("/")
def index():
    hero = db.session.scalar(
        _published_posts()
        .order_by(Post.is_top.desc(), Post.published_at.desc(), Post.id.desc())
        .limit(1)
    )
    latest_stmt = _published_posts().order_by(
        Post.is_top.desc(), Post.published_at.desc(), Post.id.desc()
    )
    if hero:
        latest_stmt = latest_stmt.where(Post.id != hero.id)
    latest_posts = db.session.scalars(latest_stmt.limit(6)).unique().all()

    popular_posts = db.session.scalars(
        _published_posts().order_by(Post.view_count.desc(), Post.published_at.desc()).limit(4)
    ).unique().all()

    category_rows = db.session.execute(
        select(Category, func.count(Post.id).label("post_count"))
        .outerjoin(
            Post,
            and_(Post.category_id == Category.id, Post.status == "published"),
        )
        .group_by(Category.id)
        .order_by(Category.sort_order.asc(), Category.id.asc())
    ).all()

    tag_rows = db.session.execute(
        select(Tag, func.count(Post.id).label("post_count"))
        .join(Tag.posts)
        .where(Post.status == "published")
        .group_by(Tag.id)
        .order_by(func.count(Post.id).desc(), Tag.name.asc())
        .limit(12)
    ).all()

    author = db.session.scalar(
        select(User).where(User.role == "admin", User.is_active.is_(True)).order_by(User.id)
    )
    stats = _site_stats()
    return render_template(
        "main/index.html",
        hero=hero,
        latest_posts=latest_posts,
        popular_posts=popular_posts,
        category_rows=category_rows,
        tag_rows=tag_rows,
        author=author,
        stats=stats,
    )


@main_bp.route("/posts")
def posts():
    q = (request.args.get("q") or "").strip()[:80]
    category_id = request.args.get("category", type=int)
    tag_id = request.args.get("tag", type=int)
    page = max(1, request.args.get("page", 1, type=int))

    stmt = _published_posts()
    active_category = None
    active_tag = None

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Post.title.ilike(pattern),
                Post.summary.ilike(pattern),
                Post.content_md.ilike(pattern),
            )
        )
    if category_id:
        active_category = db.session.get(Category, category_id)
        stmt = stmt.where(Post.category_id == category_id)
    if tag_id:
        active_tag = db.session.get(Tag, tag_id)
        stmt = stmt.join(Post.tags).where(Tag.id == tag_id)

    stmt = stmt.order_by(Post.is_top.desc(), Post.published_at.desc(), Post.id.desc())
    pagination = db.paginate(
        stmt,
        page=page,
        per_page=current_app.config["POSTS_PER_PAGE"],
        error_out=False,
        max_per_page=50,
    )

    categories = db.session.scalars(
        select(Category).order_by(Category.sort_order, Category.id)
    ).all()
    tags = db.session.scalars(
        select(Tag).join(Tag.posts).where(Post.status == "published").distinct().order_by(Tag.name)
    ).all()

    if q:
        page_title = f"搜索「{q}」"
    elif active_category:
        page_title = f"分类：{active_category.name}"
    elif active_tag:
        page_title = f"标签：#{active_tag.name}"
    else:
        page_title = "全部文章"

    return render_template(
        "main/posts.html",
        pagination=pagination,
        posts=pagination.items,
        q=q,
        active_category=active_category,
        active_tag=active_tag,
        categories=categories,
        tags=tags,
        page_title=page_title,
    )


@main_bp.route("/search")
def search():
    q = (request.args.get("q") or "").strip()[:80]
    if not q:
        flash("请输入搜索关键词。", "warning")
        return redirect(url_for("main.posts"))
    return redirect(url_for("main.posts", q=q))


@main_bp.route("/categories/<int:category_id>")
def category_filter(category_id: int):
    return redirect(url_for("main.posts", category=category_id))


@main_bp.route("/tags/<int:tag_id>")
def tag_filter(tag_id: int):
    return redirect(url_for("main.posts", tag=tag_id))


@main_bp.route("/posts/<int:post_id>")
def post_detail(post_id: int):
    post = db.session.scalar(_published_posts().where(Post.id == post_id))
    if post is None:
        # 管理员可预览草稿
        if current_user.is_authenticated and current_user.is_admin:
            post = db.session.scalar(
                select(Post).options(*POST_LOADS).where(Post.id == post_id)
            )
        if post is None:
            abort(404)

    if post.status != "published" and not (
        current_user.is_authenticated and current_user.is_admin
    ):
        abort(404)

    # 同一会话同一篇文章只计一次浏览；管理员预览不计入
    if post.status == "published" and not (
        current_user.is_authenticated and current_user.is_admin
    ):
        viewed = session.get("viewed_posts", [])
        if post.id not in viewed:
            post.view_count = (post.view_count or 0) + 1
            db.session.add(PostView(post_id=post.id, visitor_key=visitor_key()))
            viewed.append(post.id)
            session["viewed_posts"] = viewed[-30:]
            db.session.commit()

    cpage = max(1, request.args.get("cpage", 1, type=int))
    comment_stmt = (
        select(Comment)
        .where(Comment.post_id == post.id, Comment.status == "approved")
        .options(joinedload(Comment.user))
        .order_by(Comment.created_at.desc())
    )
    comments = db.paginate(
        comment_stmt,
        page=cpage,
        per_page=current_app.config["COMMENTS_PER_PAGE"],
        error_out=False,
        max_per_page=50,
    )

    favorite_count = db.session.scalar(
        select(func.count()).select_from(Favorite).where(Favorite.post_id == post.id)
    ) or 0
    favorited = (
        current_user.is_authenticated
        and post.is_favorited_by(current_user)
    )

    related = []
    if post.category_id:
        related = db.session.scalars(
            _published_posts()
            .where(Post.category_id == post.category_id, Post.id != post.id)
            .order_by(Post.published_at.desc())
            .limit(3)
        ).unique().all()

    prev_post = None
    next_post = None
    if post.published_at:
        prev_post = db.session.scalar(
            _published_posts()
            .where(Post.published_at < post.published_at)
            .order_by(Post.published_at.desc())
            .limit(1)
        )
        next_post = db.session.scalar(
            _published_posts()
            .where(Post.published_at > post.published_at)
            .order_by(Post.published_at.asc())
            .limit(1)
        )

    return render_template(
        "main/post_detail.html",
        post=post,
        comments=comments,
        favorite_count=favorite_count,
        favorited=favorited,
        related=related,
        prev_post=prev_post,
        next_post=next_post,
    )


@main_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
def comment_create(post_id: int):
    post = db.session.scalar(
        select(Post).where(Post.id == post_id, Post.status == "published")
    )
    if not post:
        abort(404)

    # 蜜罐字段：正常用户看不见，机器人往往填写
    if (request.form.get("website") or "").strip():
        flash("评论已提交，审核通过后会展示。", "success")
        return redirect(url_for("main.post_detail", post_id=post.id, _anchor="comments"))

    content = (request.form.get("content") or "").strip()
    guest_name = (request.form.get("guest_name") or "").strip()
    guest_email = (request.form.get("guest_email") or "").strip().lower()

    errors = []
    if not 2 <= len(content) <= 800:
        errors.append("评论内容需为 2–800 个字符。")
    if not current_user.is_authenticated:
        if not 2 <= len(guest_name) <= 20:
            errors.append("请填写 2–20 个字符的昵称。")
        if guest_email and not is_valid_email(guest_email):
            errors.append("邮箱格式不正确。")
    if errors:
        for message in errors:
            flash(message, "danger")
        return redirect(url_for("main.post_detail", post_id=post.id, _anchor="comment-form"))

    # 简易防刷：同一会话 20 秒内只能发一条
    last_at = session.get("last_comment_at")
    if last_at and datetime.now().timestamp() - last_at < 20:
        flash("评论太频繁啦，请稍后再试。", "warning")
        return redirect(url_for("main.post_detail", post_id=post.id, _anchor="comments"))

    comment = Comment(
        post_id=post.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        guest_name=None if current_user.is_authenticated else guest_name,
        guest_email=None if current_user.is_authenticated else (guest_email or None),
        content=content,
        status="pending",
        ip_hash=visitor_key(),
    )
    db.session.add(comment)
    db.session.commit()
    session["last_comment_at"] = datetime.now().timestamp()
    flash("评论已提交，审核通过后会展示在小栈里。", "success")
    return redirect(url_for("main.post_detail", post_id=post.id, _anchor="comments"))


@main_bp.route("/posts/<int:post_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(post_id: int):
    post = db.session.scalar(
        select(Post).where(Post.id == post_id, Post.status == "published")
    )
    if not post:
        abort(404)

    favorite = db.session.scalar(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.post_id == post.id
        )
    )
    if favorite:
        db.session.delete(favorite)
        flash("已取消收藏。", "info")
    else:
        db.session.add(Favorite(user_id=current_user.id, post_id=post.id))
        flash("已收藏到「我的收藏」。", "success")
    db.session.commit()

    next_url = request.form.get("next")
    if is_safe_url(next_url):
        return redirect(next_url)
    return redirect(url_for("main.post_detail", post_id=post.id))


@main_bp.route("/about")
def about():
    author = db.session.scalar(
        select(User).where(User.role == "admin", User.is_active.is_(True)).order_by(User.id)
    )
    stats = _site_stats()
    categories = db.session.scalars(
        select(Category).order_by(Category.sort_order, Category.id)
    ).all()
    return render_template(
        "main/about.html", author=author, stats=stats, categories=categories
    )
