-- =====================================================================
-- 我的知识小栈 · MySQL 8.0 建表脚本
-- 字符集：utf8mb4 / utf8mb4_0900_ai_ci
-- 存储引擎：InnoDB
-- 说明：
--   1. 推荐使用 `mysql -u root -p < database/schema.sql` 执行；
--   2. 执行后设置 .env 的 DATABASE_URL，再运行 `flask seed-demo` 生成演示数据；
--   3. 所有时间字段存储服务器本地时间，Docker 环境统一 TZ=Asia/Shanghai。
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `knowledge_stack`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `knowledge_stack`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `post_views`;
DROP TABLE IF EXISTS `attachments`;
DROP TABLE IF EXISTS `favorites`;
DROP TABLE IF EXISTS `comments`;
DROP TABLE IF EXISTS `post_tags`;
DROP TABLE IF EXISTS `posts`;
DROP TABLE IF EXISTS `tags`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. 用户表：admin=博主管理员；reader=注册读者
-- ---------------------------------------------------------------------
CREATE TABLE `users` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username`      VARCHAR(50)  NOT NULL COMMENT '登录用户名，3-20位字母数字下划线',
  `email`         VARCHAR(120) NOT NULL COMMENT '邮箱，可用于登录',
  `password_hash` VARCHAR(255) NOT NULL COMMENT 'Werkzeug 密码哈希，绝不存明文',
  `display_name`  VARCHAR(50)  NOT NULL COMMENT '展示昵称',
  `avatar`        VARCHAR(255) DEFAULT NULL COMMENT '头像URL，空则显示昵称首字母',
  `bio`           VARCHAR(255) DEFAULT NULL COMMENT '个人简介',
  `role`          VARCHAR(20)  NOT NULL DEFAULT 'reader' COMMENT '角色：admin/reader',
  `is_active`     TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '是否启用：1是 0否',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  `last_login_at` DATETIME     DEFAULT NULL COMMENT '最后登录时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`),
  UNIQUE KEY `uk_users_email` (`email`),
  KEY `idx_users_role` (`role`),
  CONSTRAINT `chk_users_role` CHECK (`role` IN ('admin', 'reader'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';

-- ---------------------------------------------------------------------
-- 2. 分类表：一篇文章最多一个分类
-- ---------------------------------------------------------------------
CREATE TABLE `categories` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name`        VARCHAR(50)  NOT NULL COMMENT '分类名称，唯一',
  `description` VARCHAR(255) DEFAULT NULL COMMENT '分类说明',
  `color`       VARCHAR(20)  NOT NULL DEFAULT '#1f6f5c' COMMENT '主题色，HEX格式',
  `sort_order`  INT          NOT NULL DEFAULT 0 COMMENT '排序值，越小越靠前',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_categories_name` (`name`),
  KEY `idx_categories_sort` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='文章分类表';

-- ---------------------------------------------------------------------
-- 3. 标签表：与文章多对多
-- ---------------------------------------------------------------------
CREATE TABLE `tags` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `name`       VARCHAR(40)  NOT NULL COMMENT '标签名称，唯一',
  `color`      VARCHAR(20)  NOT NULL DEFAULT '#64748b' COMMENT '标签色，HEX格式',
  `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tags_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='文章标签表';

-- ---------------------------------------------------------------------
-- 4. 文章表
-- ---------------------------------------------------------------------
CREATE TABLE `posts` (
  `id`           INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文章ID',
  `title`        VARCHAR(150) NOT NULL COMMENT '标题',
  `summary`      VARCHAR(300) DEFAULT NULL COMMENT '摘要，为空时由正文自动截取',
  `content_md`   LONGTEXT     NOT NULL COMMENT 'Markdown原文',
  `content_html` LONGTEXT     NOT NULL COMMENT '服务端渲染并过滤后的HTML',
  `cover_image`  VARCHAR(500) DEFAULT NULL COMMENT '封面图URL，空则使用默认SVG',
  `category_id`  INT UNSIGNED DEFAULT NULL COMMENT '所属分类，删除分类时置空',
  `author_id`    INT UNSIGNED NOT NULL COMMENT '作者（博主）ID',
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'draft' COMMENT '状态：draft/published',
  `is_top`       TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否置顶：1是 0否',
  `view_count`   INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计浏览量（冗余字段，便于排序）',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `published_at` DATETIME     DEFAULT NULL COMMENT '发布时间，草稿为NULL',
  PRIMARY KEY (`id`),
  KEY `idx_posts_status_published` (`status`, `published_at`),
  KEY `idx_posts_category` (`category_id`),
  KEY `idx_posts_author` (`author_id`),
  KEY `idx_posts_top` (`is_top`),
  CONSTRAINT `fk_posts_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_posts_author` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_posts_status` CHECK (`status` IN ('draft', 'published'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='文章/笔记表';

-- ---------------------------------------------------------------------
-- 5. 文章-标签关联表
-- ---------------------------------------------------------------------
CREATE TABLE `post_tags` (
  `post_id` INT UNSIGNED NOT NULL COMMENT '文章ID',
  `tag_id`  INT UNSIGNED NOT NULL COMMENT '标签ID',
  PRIMARY KEY (`post_id`, `tag_id`),
  KEY `idx_post_tags_tag` (`tag_id`),
  CONSTRAINT `fk_post_tags_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_post_tags_tag`  FOREIGN KEY (`tag_id`)  REFERENCES `tags` (`id`)  ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='文章标签关联表';

-- ---------------------------------------------------------------------
-- 6. 评论表：支持注册读者与游客；status 默认 pending
-- ---------------------------------------------------------------------
CREATE TABLE `comments` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '评论ID',
  `post_id`     INT UNSIGNED NOT NULL COMMENT '所属文章ID',
  `user_id`     INT UNSIGNED DEFAULT NULL COMMENT '注册用户ID；游客为NULL',
  `guest_name`  VARCHAR(50)  DEFAULT NULL COMMENT '游客昵称',
  `guest_email` VARCHAR(120) DEFAULT NULL COMMENT '游客邮箱，仅管理员可见',
  `content`     TEXT         NOT NULL COMMENT '评论内容，2-800字',
  `status`      VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT 'pending/approved/rejected',
  `ip_hash`     VARCHAR(64)  DEFAULT NULL COMMENT 'IP+UA哈希，不存原始IP',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
  `audited_at`  DATETIME     DEFAULT NULL COMMENT '审核时间',
  `audited_by`  INT UNSIGNED DEFAULT NULL COMMENT '审核人ID',
  PRIMARY KEY (`id`),
  KEY `idx_comments_post_status` (`post_id`, `status`),
  KEY `idx_comments_created` (`created_at`),
  KEY `idx_comments_user` (`user_id`),
  CONSTRAINT `fk_comments_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_comments_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_comments_auditor` FOREIGN KEY (`audited_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `chk_comments_status` CHECK (`status` IN ('pending', 'approved', 'rejected'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='评论表';

-- ---------------------------------------------------------------------
-- 7. 收藏表：联合主键防止重复收藏
-- ---------------------------------------------------------------------
CREATE TABLE `favorites` (
  `user_id`    INT UNSIGNED NOT NULL COMMENT '用户ID',
  `post_id`    INT UNSIGNED NOT NULL COMMENT '文章ID',
  `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  PRIMARY KEY (`user_id`, `post_id`),
  KEY `idx_favorites_post` (`post_id`),
  KEY `idx_favorites_created` (`created_at`),
  CONSTRAINT `fk_favorites_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_favorites_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='文章收藏表';

-- ---------------------------------------------------------------------
-- 8. 图片附件表
-- ---------------------------------------------------------------------
CREATE TABLE `attachments` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '附件ID',
  `user_id`       INT UNSIGNED NOT NULL COMMENT '上传者ID',
  `original_name` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `stored_name`   VARCHAR(255) NOT NULL COMMENT 'UUID存储文件名，防重名',
  `file_path`     VARCHAR(500) NOT NULL COMMENT '相对 static 的路径，如 uploads/2026/10/xx.png',
  `mime_type`     VARCHAR(100) NOT NULL COMMENT 'MIME类型',
  `file_size`     INT UNSIGNED NOT NULL COMMENT '文件大小（字节）',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_attachments_stored` (`stored_name`),
  KEY `idx_attachments_user` (`user_id`),
  KEY `idx_attachments_created` (`created_at`),
  CONSTRAINT `fk_attachments_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='图片附件表';

-- ---------------------------------------------------------------------
-- 9. 浏览明细表：数据看板 7 日趋势的数据来源
-- ---------------------------------------------------------------------
CREATE TABLE `post_views` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '浏览记录ID',
  `post_id`     INT UNSIGNED NOT NULL COMMENT '文章ID',
  `visitor_key` VARCHAR(64) DEFAULT NULL COMMENT '访客标识哈希（IP+UA），不存原始IP',
  `viewed_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
  PRIMARY KEY (`id`),
  KEY `idx_views_post_time` (`post_id`, `viewed_at`),
  KEY `idx_views_time` (`viewed_at`),
  CONSTRAINT `fk_views_post` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='文章浏览明细表';

-- =====================================================================
-- 可选：仅创建分类/标签基础字典（文章由 Flask CLI 生成）
-- =====================================================================
-- INSERT INTO categories (name, description, color, sort_order) VALUES
--   ('后端之道', 'Flask、接口设计与服务端工程实践', '#1f6f5c', 1),
--   ('前端手记', 'HTML / CSS / JavaScript 与界面细节', '#3b6ea8', 2),
--   ('数据库', 'MySQL、SQL 与数据建模', '#0f766e', 3),
--   ('学习方法', '复盘、效率与个人知识管理', '#c96f3b', 4),
--   ('生活随笔', '代码之外的观察与记录', '#8b5cf6', 5);
