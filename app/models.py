"""ORM 数据模型。

表结构与 database/schema.sql 保持一致，字段含义见数据库设计文档。
"""
from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.dialects.mysql import LONGTEXT

from .extensions import db

# MySQL 下正文使用 LONGTEXT，SQLite 下自动退化为 TEXT
LongText = db.Text().with_variant(LONGTEXT(), "mysql")


post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    db.Index("idx_post_tags_tag", "tag_id"),
)


class User(UserMixin, db.Model):
    """用户：admin=博主（站点管理员），reader=注册读者。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = db.Column(db.String(50), unique=True, nullable=False, index=True, comment="登录用户名")
    email = db.Column(db.String(120), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = db.Column(db.String(255), nullable=False, comment="密码哈希（Werkzeug）")
    display_name = db.Column(db.String(50), nullable=False, comment="展示昵称")
    avatar = db.Column(db.String(255), nullable=True, comment="头像URL，为空时显示首字母")
    bio = db.Column(db.String(255), nullable=True, comment="个人简介")
    role = db.Column(db.String(20), nullable=False, default="reader", comment="角色：admin/reader")
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment="是否启用")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="注册时间")
    last_login_at = db.Column(db.DateTime, nullable=True, comment="最后登录时间")

    posts = db.relationship("Post", back_populates="author", lazy="dynamic")
    comments = db.relationship(
        "Comment",
        back_populates="user",
        foreign_keys="Comment.user_id",
        lazy="dynamic",
    )
    favorites = db.relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    attachments = db.relationship("Attachment", back_populates="user", lazy="dynamic")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def initials(self) -> str:
        return (self.display_name or self.username or "?")[0].upper()

    def set_password(self, raw_password: str) -> None:
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Category(db.Model):
    """文章分类，一篇文章最多属于一个分类。"""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = db.Column(db.String(50), unique=True, nullable=False, comment="分类名称")
    description = db.Column(db.String(255), nullable=True, comment="分类说明")
    color = db.Column(db.String(20), nullable=False, default="#1f6f5c", comment="主题色 HEX")
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment="排序值，越小越靠前")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="创建时间")

    posts = db.relationship("Post", back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Tag(db.Model):
    """文章标签，多对多关系。"""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="标签ID")
    name = db.Column(db.String(40), unique=True, nullable=False, comment="标签名称")
    color = db.Column(db.String(20), nullable=False, default="#64748b", comment="标签色 HEX")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="创建时间")

    posts = db.relationship(
        "Post", secondary=post_tags, back_populates="tags", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class Post(db.Model):
    """博客 / 笔记文章。"""

    __tablename__ = "posts"
    __table_args__ = (
        db.Index("idx_posts_status_published", "status", "published_at"),
        db.Index("idx_posts_category", "category_id"),
        db.Index("idx_posts_author", "author_id"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="文章ID")
    title = db.Column(db.String(150), nullable=False, comment="标题")
    summary = db.Column(db.String(300), nullable=True, comment="摘要")
    content_md = db.Column(LongText, nullable=False, comment="Markdown 原文")
    content_html = db.Column(LongText, nullable=False, comment="过滤后的 HTML")
    cover_image = db.Column(db.String(500), nullable=True, comment="封面图URL")
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="draft", comment="draft/published")
    is_top = db.Column(db.Boolean, nullable=False, default=False, comment="是否置顶")
    view_count = db.Column(db.Integer, nullable=False, default=0, comment="累计浏览量")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )
    published_at = db.Column(db.DateTime, nullable=True, index=True, comment="发布时间")

    author = db.relationship("User", back_populates="posts")
    category = db.relationship("Category", back_populates="posts")
    tags = db.relationship(
        "Tag", secondary=post_tags, back_populates="posts", order_by="Tag.name"
    )
    comments = db.relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    favorites = db.relationship(
        "Favorite", back_populates="post", cascade="all, delete-orphan"
    )
    views = db.relationship(
        "PostView", back_populates="post", cascade="all, delete-orphan"
    )

    @property
    def is_published(self) -> bool:
        return self.status == "published"

    @property
    def status_label(self) -> str:
        return {"published": "已发布", "draft": "草稿"}.get(self.status, self.status)

    @property
    def reading_minutes(self) -> int:
        """按中文 400 字/分钟粗略估算阅读时长。"""
        plain = self.content_md or ""
        return max(1, round(len(plain) / 400))

    @property
    def cover_url(self) -> str:
        return self.cover_image or "/static/img/covers/cover-default.svg"

    @property
    def approved_comment_count(self) -> int:
        return sum(1 for item in self.comments if item.status == "approved")

    def is_favorited_by(self, user) -> bool:
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return (
            db.session.scalar(
                db.select(Favorite.user_id).where(
                    Favorite.user_id == user.id, Favorite.post_id == self.id
                )
            )
            is not None
        )

    def __repr__(self) -> str:
        return f"<Post {self.id} {self.title}>"


class Comment(db.Model):
    """评论：支持登录读者与游客，默认待审核。"""

    __tablename__ = "comments"
    __table_args__ = (
        db.Index("idx_comments_post_status", "post_id", "status"),
        db.Index("idx_comments_created", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="评论ID")
    post_id = db.Column(
        db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    guest_name = db.Column(db.String(50), nullable=True, comment="游客昵称")
    guest_email = db.Column(db.String(120), nullable=True, comment="游客邮箱，不公开")
    content = db.Column(db.Text, nullable=False, comment="评论内容")
    status = db.Column(
        db.String(20), nullable=False, default="pending", comment="pending/approved/rejected"
    )
    ip_hash = db.Column(db.String(64), nullable=True, comment="IP+UA 的哈希，用于风控")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="提交时间")
    audited_at = db.Column(db.DateTime, nullable=True, comment="审核时间")
    audited_by = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    post = db.relationship("Post", back_populates="comments")
    user = db.relationship("User", back_populates="comments", foreign_keys=[user_id])
    auditor = db.relationship("User", foreign_keys=[audited_by])

    @property
    def display_name(self) -> str:
        if self.user:
            return self.user.display_name
        return self.guest_name or "匿名访客"

    @property
    def initials(self) -> str:
        return self.display_name[0].upper()

    @property
    def status_label(self) -> str:
        return {"pending": "待审核", "approved": "已通过", "rejected": "已驳回"}.get(
            self.status, self.status
        )

    def __repr__(self) -> str:
        return f"<Comment {self.id} post={self.post_id}>"


class Favorite(db.Model):
    """用户收藏，联合主键避免重复收藏。"""

    __tablename__ = "favorites"
    __table_args__ = (
        db.PrimaryKeyConstraint("user_id", "post_id", name="pk_favorites"),
        db.Index("idx_favorites_post", "post_id"),
        db.Index("idx_favorites_created", "created_at"),
    )

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id = db.Column(
        db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="收藏时间")

    user = db.relationship("User", back_populates="favorites")
    post = db.relationship("Post", back_populates="favorites")


class Attachment(db.Model):
    """图片附件元数据，实际文件保存于 static/uploads/ 下。"""

    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="附件ID")
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_name = db.Column(db.String(255), nullable=False, comment="原始文件名")
    stored_name = db.Column(db.String(255), unique=True, nullable=False, comment="UUID存储名")
    file_path = db.Column(db.String(500), nullable=False, comment="相对 static 的路径")
    mime_type = db.Column(db.String(100), nullable=False, comment="MIME类型")
    file_size = db.Column(db.Integer, nullable=False, comment="字节数")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="上传时间")

    user = db.relationship("User", back_populates="attachments")

    @property
    def url(self) -> str:
        return f"/static/{self.file_path}"

    @property
    def size_kb(self) -> int:
        return max(1, round((self.file_size or 0) / 1024))

    def __repr__(self) -> str:
        return f"<Attachment {self.id} {self.original_name}>"


class PostView(db.Model):
    """文章浏览明细，用于数据看板的 7 日访问趋势。"""

    __tablename__ = "post_views"
    __table_args__ = (
        db.Index("idx_views_post_time", "post_id", "viewed_at"),
        db.Index("idx_views_time", "viewed_at"),
    )

    # SQLite 只有 INTEGER PRIMARY KEY 才会自增，MySQL 使用 BIGINT
    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        comment="浏览记录ID",
    )
    post_id = db.Column(
        db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    visitor_key = db.Column(db.String(64), nullable=True, comment="访客标识哈希")
    viewed_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="浏览时间")

    post = db.relationship("Post", back_populates="views")
