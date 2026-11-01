# 我的知识小栈 · 个人博客 / 笔记管理系统

> 高校软件课程综合训练项目 · Flask + MySQL 8.0 + 原生 HTML/CSS/JavaScript
>
> 把零散的知识，收进一座会生长的小栈。

一个可以直接运行、可以部署、可以课堂路演的完整个人知识管理项目。它不只是“能增删改查”的课程作业：包含博主后台、Markdown 编辑器、评论审核、收藏、图片附件、访问数据看板、浅色/暗黑双主题，以及完整的需求、数据库、概要设计、接口、GitHub 协作、路演与总结材料。

![项目封面](app/static/img/covers/cover-notes.svg)

---

## 1. 功能一览

### 1.1 主体基础功能（必做）

| 编号 | 功能 | 实现说明 |
| --- | --- | --- |
| F1 | 用户登录 / 注册 | Flask-Login 会话认证；博主由 CLI 创建，公开注册默认为读者；密码 Werkzeug 哈希 |
| F2 | 文章发布 / 编辑 / 删除 / 修改 | 后台文章 CRUD，支持草稿与发布两种状态，删除有二次确认 |
| F3 | 分类管理 / 标签管理 | 分类 CRUD + 排序 + 主题色；标签 CRUD；文章可多选标签，也支持编辑时新建标签 |
| F4 | 文章浏览 / 分页 / 详情 | 首页推荐、全部文章、分类/标签筛选、分页、详情页、上下篇、相关文章 |
| F5 | 文章搜索 | 标题、摘要、正文 `LIKE` 检索；支持关键词 + 分类 + 标签组合筛选 |

### 1.2 扩展加分功能

| 编号 | 功能 | 实现说明 |
| --- | --- | --- |
| E1 | Markdown 编辑器 | 工具栏 + 实时预览 + 快捷键 + 粘贴/拖拽上传图片；服务端渲染并用 bleach 过滤 |
| E2 | 文章收藏 | 登录读者可收藏/取消收藏，联合主键防重复；“我的收藏”分页展示 |
| E3 | 访客评论与审核 | 游客/读者均可评论，默认 `pending`；后台可通过、驳回、删除；蜜罐 + 20 秒防刷 |
| E4 | 暗黑 / 浅色主题 | 统一 CSS 变量 + `data-theme`，`localStorage` 记忆，跟随系统偏好，避免闪烁 |
| E5 | 图片附件管理 | 校验真实图片格式与尺寸、UUID 重命名、5MB 限制；后台附件库复制 Markdown/URL |
| E6 | 数据看板 | 文章数、阅读量、今日/7 日访问、待审核评论、收藏数、分类分布、热门文章、动态 |

### 1.3 角色与权限

| 角色 | 获取方式 | 权限 |
| --- | --- | --- |
| 访客 | 无需登录 | 浏览、搜索、查看详情、游客评论（待审核） |
| 读者 `reader` | 前台注册 | 访客全部权限 + 收藏、以账号身份评论、账号资料/密码、评论记录 |
| 博主 `admin` | `flask create-admin` / `seed-demo` | 全部权限 + 后台数据看板、文章/分类/标签/评论/附件管理 |

> 设计取舍：公开注册不直接授予后台权限，避免任意用户进入管理端；课程演示使用预置的 `admin` 账号。这样既保留“注册”流程，又符合个人博客只有站主能发文的产品逻辑。

---

## 2. 技术栈

| 层 | 技术 | 选择理由 |
| --- | --- | --- |
| 后端 | Python 3.12 / Flask 3 | 轻量、路由直观、适合课程项目快速部署 |
| ORM | Flask-SQLAlchemy 3 / SQLAlchemy 2 | 防止 SQL 注入，关系映射清晰，测试可切 SQLite |
| 数据库 | MySQL 8.0（utf8mb4） | 课程要求，支持事务、外键、索引；附完整 DDL |
| 认证 | Flask-Login + Werkzeug | 会话登录、密码哈希、角色校验 |
| 表单安全 | Flask-WTF CSRFProtect | 所有写操作均有 CSRF Token |
| Markdown | Python-Markdown + Bleach | 服务端统一渲染，白名单过滤存储型 XSS |
| 图片 | Pillow | 校验真实图片，防止改扩展名上传脚本 |
| 前端 | 原生 HTML5 / CSS3 / ES6 | 无 Vue/React，课堂讲解成本低；CSS 变量实现双主题 |
| 测试 | pytest | 13 个核心用例，覆盖权限、CRUD、评论、收藏、上传 |
| 部署 | Docker Compose + Gunicorn | 一条命令启动 MySQL + 应用 |

---

## 3. 快速开始

### 方式 A：Docker Compose（最省事，推荐课堂演示）

前置条件：安装 Docker Desktop。

```bash
docker compose up -d --build
```

等待 MySQL 健康检查通过后，访问：

- 前台：<http://127.0.0.1:5000>
- 后台：<http://127.0.0.1:5000/admin>
- MySQL：`127.0.0.1:3307`（容器内 3306）

首次启动会自动建表并生成演示数据。

停止 / 清空数据：

```bash
docker compose down          # 停止，保留数据卷
docker compose down -v       # 停止并删除数据库与上传文件
```

### 方式 B：本机 MySQL 8.0 + Python

#### 1）准备数据库

```sql
-- 用 root 登录 MySQL 后执行
CREATE DATABASE knowledge_stack
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

CREATE USER 'blogger'@'localhost' IDENTIFIED BY 'blogger123';
GRANT ALL PRIVILEGES ON knowledge_stack.* TO 'blogger'@'localhost';
FLUSH PRIVILEGES;
```

也可以直接执行完整建表脚本：

```bash
mysql -u root -p < database/schema.sql
```

#### 2）安装依赖

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3）配置环境变量

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

编辑 `.env`：

```dotenv
SECRET_KEY=换成一串足够长的随机字符
DATABASE_URL=mysql+pymysql://blogger:blogger123@127.0.0.1:3306/knowledge_stack?charset=utf8mb4
```

#### 4）初始化并启动

```bash
flask init-db          # 建表（如果已执行 schema.sql 可跳过）
flask seed-demo        # 生成演示数据（可重复执行；已有数据会跳过）
flask run              # 或 python run.py
```

打开 <http://127.0.0.1:5000>。

### 演示账号

| 角色 | 用户名 | 密码 | 入口 |
| --- | --- | --- | --- |
| 博主管理员 | `admin` | `Admin@123` | `/auth/login` → `/admin` |
| 注册读者 | `reader` | `Reader@123` | `/auth/login` |

> 正式部署前请修改演示密码，并在 `.env` 中设置新的 `SECRET_KEY`。

---

## 4. 常用命令

```bash
flask init-db                       # 按 ORM 模型建表
flask seed-demo                     # 生成演示数据（已有 admin 时跳过）
flask seed-demo --reset             # 清空并重建演示数据（会二次确认）
flask create-admin                  # 交互式创建博主账号
flask promote-user <username>       # 将已有读者提升为博主
pytest -q                           # 运行测试
gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app   # 生产启动
```

常用 URL：

| 页面 | 地址 |
| --- | --- |
| 首页 | `/` |
| 文章列表 / 搜索 | `/posts`、`/search?q=Flask` |
| 文章详情 | `/posts/<id>` |
| 关于 | `/about` |
| 登录 / 注册 | `/auth/login`、`/auth/register` |
| 账号中心 | `/account`、`/account/favorites` |
| 后台看板 | `/admin/dashboard` |
| 文章管理 | `/admin/posts` |
| 分类标签 | `/admin/categories`、`/admin/tags` |
| 评论审核 | `/admin/comments` |
| 图片附件 | `/admin/attachments` |

---

## 5. 项目结构

```text
.
├─ app/
│  ├─ __init__.py          # 应用工厂、模板过滤器、错误页、安全响应头
│  ├─ extensions.py        # db / login_manager / csrf
│  ├─ models.py            # 9 张表的 ORM 模型
│  ├─ auth.py              # 登录、注册、退出
│  ├─ main.py              # 首页、列表、搜索、详情、评论、收藏
│  ├─ account.py           # 账号资料、密码、收藏、评论记录
│  ├─ admin.py             # 看板、文章、分类、标签、评论、附件
│  ├─ api.py               # Markdown 预览、图片上传 JSON 接口
│  ├─ cli.py               # init-db / seed-demo / create-admin
│  ├─ utils.py             # Markdown 安全渲染、图片校验、摘要、访客标识
│  ├─ templates/           # Jinja2 模板（前台 / 后台 / 认证 / 错误页）
│  └─ static/
│     ├─ css/style.css     # 统一设计系统 + 双主题 + 响应式
│     ├─ js/app.js         # 全站交互
│     ├─ js/editor.js      # Markdown 编辑器
│     ├─ img/covers/       # 本地 SVG 封面（无外网依赖）
│     └─ uploads/          # 运行时上传目录（不提交 Git）
├─ database/schema.sql     # MySQL 8.0 完整建表 SQL
├─ docs/                   # 需求、数据库、设计、接口、GitHub、PPT、录屏、总结
├─ tests/                  # pytest 测试
├─ deliverables/           # PPTX / DOCX / 演示脚本等提交材料
├─ config.py               # 环境配置
├─ run.py / wsgi.py        # 开发 / 生产入口
├─ Dockerfile
├─ docker-compose.yml
└─ requirements.txt
```

---

## 6. 核心设计说明

### 6.1 为什么公开注册是读者？

个人博客的产品语义是“一个站主 + 多位访客”。若注册即管理员，任何访问者都能进入后台，不符合真实系统。项目保留完整注册流程，同时把角色拆成：

- 公开注册 → `reader`：收藏、评论、账号管理；
- 站主账号 → `admin`：内容与审核。

需要新增协作者时使用 `flask promote-user`，而不是开放后台权限。

### 6.2 评论为什么要审核？

访客评论默认 `pending`，后台通过后才出现在文章页。配套做了：

- 蜜罐字段拦截简单机器人；
- 同一会话 20 秒防刷；
- 内容长度、游客昵称、邮箱格式校验；
- 评论只以纯文本输出，不渲染 HTML；
- 管理员可查看游客邮箱（前台不展示）。

### 6.3 Markdown 安全链路

```text
textarea(Markdown)
  → POST /api/markdown/preview（登录 + CSRF）
  → Python-Markdown 渲染
  → Bleach 白名单过滤（标签/属性/协议）
  → 返回 HTML
  → 存入 posts.content_html
  → 详情页 |safe 输出
```

数据库同时保存 `content_md` 与 `content_html`：前者用于再次编辑和全文检索，后者用于展示，避免每次访问重复渲染。

### 6.4 浏览统计口径

- 文章详情页按“同一会话同一篇只计一次”新增 `post_views` 明细；
- `posts.view_count` 作为冗余字段，便于热门排序，避免每次聚合；
- 管理员预览草稿不计入；
- 看板 7 日趋势在 Python 侧聚合，兼容 MySQL 与测试用 SQLite。

### 6.5 主题实现

`app/static/css/style.css` 用一张变量表定义颜色、阴影、字体，`[data-theme="dark"]` 只覆盖变量；`app/static/js/app.js` 负责写入 `data-theme` 并记忆到 `localStorage`。无第二套 CSS，无组件级硬编码颜色，新增组件自动适配双主题。

---

## 7. 安全清单

- 密码只存 Werkzeug 哈希，登录失败统一提示，不泄露账号是否存在；
- 所有 POST 表单由 Flask-WTF 校验 CSRF；
- ORM 参数化查询，杜绝 SQL 拼接注入；
- Markdown 渲染后经 bleach 白名单过滤；评论按纯文本输出；
- 上传只接受真实 JPEG/PNG/GIF/WEBP（Pillow 校验），UUID 重命名，5MB 限制；
- 跳转参数经 `is_safe_url` 校验，避免开放重定向；
- 后台统一 `admin` 角色校验，读者访问返回 403；
- Cookie 设置 `HttpOnly` / `SameSite=Lax`；响应头含 `X-Content-Type-Options`、`X-Frame-Options` 等；
- 上传目录不提交 Git，`.env` 不提交 Git。

---

## 8. 测试

```bash
pytest -q
```

覆盖：

- 首页 / 文章 / 关于 / 登录注册页面渲染；
- 管理员登录与看板；
- 读者访问后台被拒绝（403）；
- 文章新增、编辑、转草稿、删除；
- 标题 / 正文搜索与空结果；
- 游客评论 → 待审核 → 管理员通过 → 前台可见；
- 收藏与取消收藏；
- 注册自动创建读者角色；
- Markdown XSS 过滤；
- 图片上传格式校验与成功上传；
- 后台 13 个页面冒烟测试；
- 未登录访问账号中心 / 后台重定向。

---

## 9. 项目文档

| 文档 | 内容 |
| --- | --- |
| [00 项目整体方案](docs/00-项目整体方案.md) | 一页看清目标、范围、技术、进度、交付物 |
| [01 项目需求文档](docs/01-项目需求文档.md) | 背景、角色、场景、功能清单、非功能需求、验收标准 |
| [02 数据库设计文档](docs/02-数据库设计文档.md) | ER 图文字描述、9 张表结构、字段说明、索引与设计取舍 |
| [03 系统概要设计与模块划分](docs/03-系统概要设计与模块划分.md) | 架构、目录、模块职责、关键流程、安全与部署 |
| [04 前端页面规划与原型说明](docs/04-前端页面规划与原型说明.md) | 页面地图、原型、设计令牌、组件、响应式、双主题 |
| [05 后端接口与业务实现](docs/05-后端接口与业务实现.md) | 路由表、请求响应、权限、错误码、关键代码 |
| [06 GitHub 协作规范](docs/06-GitHub协作规范.md) | 仓库流程、分支模型、提交规范、PR、Issue、冲突处理 |
| [07 路演 PPT 大纲](docs/07-路演PPT大纲.md) | 16 页逐页讲稿、时间分配、演示动线 |
| [08 项目录屏演示脚本](docs/08-项目录屏演示脚本.md) | 6–8 分钟分镜、旁白、操作步骤、录制参数 |
| [09 课程个人总结模板](docs/09-课程个人总结模板.md) | 可直接填写/参考的 1800 字总结模板 |
| [10 答辩问答](docs/10-答辩问答.md) | 20 个高频问题与回答要点 |
| [11 小组分工与进度计划](docs/11-小组分工与进度计划.md) | 五人/四人分工、周计划、评审与贡献记录 |

课堂提交材料在 [`deliverables/`](deliverables/) 目录：

- [小组路演 PPTX](deliverables/我的知识小栈-小组路演.pptx)（16 页，含讲者备注）
- [课程个人总结模板 DOCX](deliverables/我的知识小栈-课程个人总结模板.docx)
- [交付清单](deliverables/交付清单.md)
- [首页截图](deliverables/screenshot-home.png) / [后台看板截图](deliverables/screenshot-admin.png)

---

## 10. Git 提交约定（摘要）

```text
<type>(<scope>): <subject>

feat(post): 新增文章草稿与发布状态切换
fix(comment): 修复待审核评论在前台泄露的问题
docs(db): 补充 post_views 表索引说明
style(ui): 统一暗黑模式下的卡片边框
refactor(admin): 抽离文章表单校验函数
test(auth): 增加读者越权访问后台的用例
chore(deps): 升级 Flask 至 3.1
```

详细分支模型、PR 模板、代码评审清单见 [GitHub 协作规范](docs/06-GitHub协作规范.md)。

---

## 11. 已知边界与后续可扩展

当前版本面向课程演示，以下是有意识保留的边界：

- 搜索使用 `LIKE`，数据量上万后应改为 MySQL `FULLTEXT + ngram` 或独立搜索服务；
- 未做邮件通知、第三方登录、文章版本历史；
- 上传文件保存在本地磁盘，生产可切换对象存储；
- 未接入 Redis 缓存与异步任务；
- 单博主模型，协作者需由 CLI 提升权限。

后续可扩展：全文索引、RSS、文章系列、阅读进度、导出 PDF、对象存储、访问日志可视化。

---

## 12. 许可

本项目为课程学习用途，代码采用 [MIT License](LICENSE)。封面 SVG、演示文章均为项目原创/虚构内容。
