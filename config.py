"""应用配置。

课程项目默认连接本机 MySQL 8.0；测试环境可通过 DATABASE_URL 覆盖为 SQLite。
所有敏感配置均从环境变量读取，仓库中只保留 .env.example。
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # ---------- 基础 ----------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me-before-deploy")
    SITE_NAME = os.getenv("SITE_NAME", "我的知识小栈")
    SITE_SUBTITLE = os.getenv("SITE_SUBTITLE", "把零散的知识，收进一座会生长的小栈。")
    SITE_DESCRIPTION = os.getenv(
        "SITE_DESCRIPTION",
        "一个用于记录编程学习、项目复盘与生活灵感的个人博客 / 笔记管理系统。",
    )
    SITE_AUTHOR = os.getenv("SITE_AUTHOR", "阿栈")

    # ---------- 数据库 ----------
    # 生产 / 课程演示环境：MySQL 8.0
    # 例：mysql+pymysql://blogger:blogger123@127.0.0.1:3306/knowledge_stack?charset=utf8mb4
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://blogger:blogger123@127.0.0.1:3306/knowledge_stack?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # ---------- 会话与安全 ----------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    WTF_CSRF_TIME_LIMIT = None
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 单次请求最大 8MB

    # ---------- 上传 ----------
    UPLOAD_FOLDER = str(BASE_DIR / "app" / "static" / "uploads")
    ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "WEBP"}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 单张图片 5MB

    # ---------- 分页 ----------
    POSTS_PER_PAGE = 6
    ADMIN_PAGE_SIZE = 10
    COMMENTS_PER_PAGE = 20

    # ---------- 其他 ----------
    TIMEZONE = os.getenv("TZ", "Asia/Shanghai")


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SERVER_NAME = None
