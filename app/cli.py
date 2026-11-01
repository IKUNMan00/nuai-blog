"""Flask CLI：初始化数据库、生成演示数据、创建管理员。"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

import click
from flask import Flask
from sqlalchemy import select

from .extensions import db
from .models import Category, Comment, Favorite, Post, PostView, Tag, User
from .utils import render_markdown


def register_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        """按 ORM 模型创建全部数据表（也可直接执行 database/schema.sql）。"""
        db.create_all()
        click.echo("[OK] 数据表创建完成。")

    @app.cli.command("seed-demo")
    @click.option("--reset", is_flag=True, help="清空现有表后重新生成演示数据（危险）")
    def seed_demo_command(reset: bool):
        """生成课程演示数据：博主、读者、分类、标签、文章、评论、浏览记录。"""
        if reset:
            click.confirm("将删除当前数据库全部数据，确认继续？", abort=True)
            db.drop_all()
            db.create_all()
        elif db.session.scalar(select(User).where(User.username == "admin")):
            click.echo("检测到已有演示数据，跳过。如需重建请加 --reset。")
            return
        else:
            db.create_all()

        seed_demo()
        click.echo("[OK] 演示数据已生成。")
        click.echo("   博主：admin / Admin@123")
        click.echo("   读者：reader / Reader@123")

    @app.cli.command("create-admin")
    @click.option("--username", prompt="管理员用户名")
    @click.option("--email", prompt="管理员邮箱")
    @click.option("--display-name", prompt="展示昵称")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin_command(username: str, email: str, display_name: str, password: str):
        """创建一个博主管理员账号。"""
        if db.session.scalar(select(User).where(User.username == username)):
            click.echo("[ERROR] 用户名已存在。")
            return
        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            display_name=display_name.strip(),
            role="admin",
            bio="知识小栈的博主。",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"[OK] 管理员 {username} 创建成功。")

    @app.cli.command("promote-user")
    @click.argument("username")
    def promote_user_command(username: str):
        """把已有读者提升为博主管理员。"""
        user = db.session.scalar(select(User).where(User.username == username))
        if not user:
            click.echo("[ERROR] 用户不存在。")
            return
        user.role = "admin"
        db.session.commit()
        click.echo(f"[OK] {username} 已提升为管理员。")


def seed_demo() -> None:
    """生成一套内容完整、图表有数据、可直接路演的数据。"""
    now = datetime.now()
    rng = random.Random(20261031)

    admin = User(
        username="admin",
        email="admin@example.com",
        display_name="阿栈",
        role="admin",
        bio="软件工程专业学生，正在把每一次踩坑都写成可以复用的知识。",
        avatar=None,
        created_at=now - timedelta(days=120),
    )
    admin.set_password("Admin@123")

    reader = User(
        username="reader",
        email="reader@example.com",
        display_name="小满",
        role="reader",
        bio="喜欢在别人的经验里找答案。",
        created_at=now - timedelta(days=45),
    )
    reader.set_password("Reader@123")

    db.session.add_all([admin, reader])
    db.session.flush()

    category_specs = [
        ("后端之道", "Flask、接口设计与服务端工程实践", "#1f6f5c", 1),
        ("前端手记", "HTML / CSS / JavaScript 与界面细节", "#3b6ea8", 2),
        ("数据库", "MySQL、SQL 与数据建模", "#0f766e", 3),
        ("学习方法", "复盘、效率与个人知识管理", "#c96f3b", 4),
        ("生活随笔", "代码之外的观察与记录", "#8b5cf6", 5),
    ]
    categories = {}
    for name, description, color, order in category_specs:
        category = Category(
            name=name,
            description=description,
            color=color,
            sort_order=order,
            created_at=now - timedelta(days=110),
        )
        categories[name] = category
        db.session.add(category)

    tag_specs = {
        "Python": "#3b6ea8",
        "Flask": "#1f6f5c",
        "MySQL": "#0f766e",
        "CSS": "#c96f3b",
        "JavaScript": "#b45309",
        "Markdown": "#64748b",
        "复盘": "#8b5cf6",
        "效率": "#0ea5e9",
        "作品集": "#db2777",
    }
    tags = {}
    for name, color in tag_specs.items():
        tag = Tag(name=name, color=color, created_at=now - timedelta(days=100))
        tags[name] = tag
        db.session.add(tag)

    db.session.flush()

    post_specs = [
        {
            "title": "从零搭建一座会生长的知识栈：我的笔记方法论",
            "category": "学习方法",
            "tags": ["复盘", "效率", "Markdown"],
            "cover": "/static/img/covers/cover-notes.svg",
            "is_top": True,
            "days": 2,
            "views": 286,
            "summary": "笔记不是收藏夹，而是一套可以反复调用的思考工具。分享我用「入口—加工—出口」三层结构管理知识的方式。",
            "content": """## 为什么笔记越记越乱？

刚开始学编程时，我的收藏夹里有上百个链接：教程、报错截图、别人写的项目模板。真正遇到问题时，却一个都想不起来。问题不在工具，而在于**只做了收集，没有做加工**。

> 知识管理的目标不是“拥有更多资料”，而是“在需要的时候，能更快地做出判断”。

## 我的三层知识栈

我把每条笔记放进三个抽屉：

1. **入口层**：临时想法、链接、课堂速记。允许粗糙，但要标注来源。
2. **加工层**：用自己的话解释概念，补上例子、反例和适用边界。
3. **出口层**：能直接复用的清单、代码片段、复盘文章或项目说明。

### 一条笔记的最小结构

```markdown
# 标题：一句话说清这条笔记解决什么问题
- 场景：
- 结论：
- 证据 / 代码：
- 反例：
- 还能用在哪里：
```

这个结构看起来笨，但它强迫我回答三个问题：**我在什么场景下会用到它？我凭什么相信它？它还能迁移到哪里？**

## 每周一次“小栈盘点”

每周日晚上花 30 分钟：

- 删除已经失效的链接；
- 把 3 条临时笔记加工成永久笔记；
- 从永久笔记里挑 1 条，写成可以公开发布的文章；
- 给下周留一个明确的问题，而不是一堆待办。

| 动作 | 频率 | 产出 |
| --- | --- | --- |
| 收集 | 随时 | 入口笔记 |
| 加工 | 每周 | 概念卡 / 代码卡 |
| 输出 | 每两周 | 博客文章 / 项目复盘 |

## 最后

工具会过时，结构不会。先让笔记能回答一个真实问题，再考虑把它做得漂亮。""",
        },
        {
            "title": "Flask 应用工厂：把项目拆成可维护的积木",
            "category": "后端之道",
            "tags": ["Python", "Flask"],
            "cover": "/static/img/covers/cover-code.svg",
            "is_top": False,
            "days": 5,
            "views": 198,
            "summary": "从单文件 app.py 到可测试的应用工厂：蓝图、扩展初始化、配置分层，一次讲清楚。",
            "content": """## 为什么不直接写一个 app.py？

课程项目最初只有一个文件：路由、数据库、配置全部挤在一起。功能一多，改一处就可能影响另一处。**应用工厂**把“创建应用”和“使用应用”分开，让测试、部署和多环境配置都更从容。

```python
# app/__init__.py
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    from .main import main_bp
    app.register_blueprint(main_bp)
    return app
```

## 三个关键收益

### 1. 测试可以拥有独立数据库

```python
app = create_app({
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
})
```

测试不会碰生产数据，也不需要启动 MySQL。

### 2. 配置与代码解耦

数据库地址、密钥、上传目录全部从环境变量读取。仓库里只提交 `.env.example`，真实密钥留在部署机器上。

### 3. 蓝图负责“按业务切块”

- `main`：公开页面
- `auth`：登录注册
- `admin`：后台管理
- `api`：JSON 接口

每个模块只关心自己的路由和模板，团队协作时冲突更少。

## 一个容易忽略的细节

在工厂函数内部再导入蓝图，可以避免循环导入：

```python
from .models import User  # 此时 db 已经初始化
```

## 复盘

应用工厂不是“高级技巧”，而是把项目从**能跑**推向**能维护**的第一步。先拆边界，再谈优化。""",
        },
        {
            "title": "MySQL 8.0 字符集与索引：中文博客避坑清单",
            "category": "数据库",
            "tags": ["MySQL"],
            "cover": "/static/img/covers/cover-data.svg",
            "is_top": False,
            "days": 8,
            "views": 167,
            "summary": "emoji 乱码、中文排序、LIKE 搜索慢——三个真实问题背后的字符集与索引知识。",
            "content": """## 建库时的三个决定

```sql
CREATE DATABASE knowledge_stack
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
```

- `utf8mb4` 才能保存 emoji 和完整的中文；
- `utf8mb4_0900_ai_ci` 是 MySQL 8.0 的默认排序规则，`ai` 表示不区分重音，`ci` 表示不区分大小写；
- 连接串也要带 `charset=utf8mb4`，否则客户端和服务端可能各说各话。

## LIKE 搜索的边界

课程项目里，标题和正文搜索用了：

```sql
SELECT * FROM posts
WHERE status = 'published'
  AND (title LIKE '%Flask%' OR content_md LIKE '%Flask%');
```

它能满足演示，但有两个限制：

1. 前置通配符 `%` 让普通 B-Tree 索引失效；
2. 数据量上万后，全表扫描会明显变慢。

进一步可以选：

- MySQL `FULLTEXT` + `ngram` 解析器（支持中文）；
- 独立搜索引擎（Elasticsearch / Meilisearch）；
- 应用层缓存高频搜索词。

> 先量数据，再选方案。不要为了“看起来高级”提前引入复杂组件。

## 索引不是越多越好

| 查询场景 | 建议索引 |
| --- | --- |
| 首页按状态 + 发布时间排序 | `(status, published_at)` |
| 分类页 | `category_id` |
| 评论区按文章 + 状态 | `(post_id, status)` |
| 收藏判重 | `(user_id, post_id)` 联合主键 |

每个索引都会增加写入成本。先写清楚高频查询，再决定加什么。""",
        },
        {
            "title": "CSS 变量 + data-theme：一次编写，双主题生效",
            "category": "前端手记",
            "tags": ["CSS", "JavaScript"],
            "cover": "/static/img/covers/cover-design.svg",
            "is_top": False,
            "days": 12,
            "views": 241,
            "summary": "不引入 UI 框架，只用 CSS 自定义属性和一行 data-theme，完成浅色 / 暗黑主题与动效降级。",
            "content": """## 先定义“设计变量”

```css
:root {
  --bg: #f6f4ef;
  --surface: #fffdf9;
  --text: #1c2520;
  --brand: #1f6f5c;
  --line: rgba(28, 37, 32, .12);
}

[data-theme="dark"] {
  --bg: #111816;
  --surface: #17211d;
  --text: #e8efe9;
  --brand: #78c7ac;
  --line: rgba(232, 239, 233, .14);
}
```

所有组件只使用变量，不写死颜色。这样切换主题时，浏览器只需要重新计算变量。

## 一行脚本避免闪烁

主题脚本放在 `<head>` 中、CSS 之后立即执行，避免页面先白后黑：

```javascript
const saved = localStorage.getItem("theme");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
document.documentElement.dataset.theme = saved || (prefersDark ? "dark" : "light");
```

## 可访问性不能忘

- 切换按钮使用 `aria-pressed` 表达状态；
- 焦点样式必须清晰可见；
- 对 `prefers-reduced-motion` 用户关闭非必要动画；
- 正文与背景的对比度至少达到 WCAG AA。

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
```

## 小结

主题切换的本质不是“两套 CSS”，而是**一套语义化的设计令牌**。变量命名越接近用途，组件越容易复用。""",
        },
        {
            "title": "写好一篇技术复盘：从流水账到可复用经验",
            "category": "学习方法",
            "tags": ["复盘", "效率"],
            "cover": "/static/img/covers/cover-default.svg",
            "is_top": False,
            "days": 16,
            "views": 132,
            "summary": "复盘不是把过程再讲一遍，而是提炼出下次能直接使用的判断和清单。",
            "content": """## 流水账的问题

“今天安装了 Flask，遇到了报错，后来解决了。”这不是复盘，只是日记。读者无法判断：什么环境？报错信息是什么？为什么那样解决？下次遇到同类问题怎么办？

## 一个可复用的复盘模板

### 1. 背景与目标

用三句话说明：做什么、为什么做、做到什么程度算完成。

### 2. 关键决策

列出 1–3 个真正影响结果的决策，并写出被放弃的方案。

### 3. 证据

保留最小可复现信息：

- 环境版本；
- 关键代码；
- 报错原文；
- 验证方式。

### 4. 可迁移的结论

把“这次怎么做”上升为“什么情况下应该怎么做”。

> 好的复盘让未来的自己少走一次弯路，也让同伴不必重复踩坑。

## 发布前检查

- 标题是否说明了具体问题？
- 代码块是否可复制？
- 有没有把“结论”和“猜测”分开？
- 有没有留下参考链接？

写复盘不是为了证明自己努力，而是为了把经验变成公共资产。""",
        },
        {
            "title": "原生 JavaScript 也能做出顺滑交互",
            "category": "前端手记",
            "tags": ["JavaScript", "CSS"],
            "cover": "/static/img/covers/cover-code.svg",
            "is_top": False,
            "days": 21,
            "views": 154,
            "summary": "主题切换、搜索弹窗、Markdown 实时预览、上传进度：不引入框架，也能把细节做好。",
            "content": """## 少一点依赖，多一点理解

课程项目没有使用 Vue / React，并不是拒绝框架，而是希望先把浏览器原生能力用熟。以下四个交互都只用了原生 API。

### 搜索弹窗：`<dialog>`

```html
<dialog id="search-dialog">
  <form method="get" action="/search">
    <input name="q" placeholder="搜索文章…">
  </form>
</dialog>
```

```javascript
const dialog = document.querySelector("#search-dialog");
document.querySelector("[data-open-search]").addEventListener("click", () => {
  dialog.showModal();
  dialog.querySelector("input").focus();
});
```

`dialog` 自带焦点管理和 Esc 关闭，比手写遮罩层更稳。

### Markdown 预览：防抖 + fetch

```javascript
let timer;
editor.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(preview, 350);
});
```

每次输入都请求接口会浪费资源，350ms 防抖足够平衡实时性和性能。

### 上传图片：FormData

```javascript
const data = new FormData();
data.append("file", file);
const response = await fetch("/api/upload", {
  method: "POST",
  headers: { "X-CSRFToken": csrfToken },
  body: data,
});
```

### 主题切换：只改一个属性

```javascript
document.documentElement.dataset.theme = nextTheme;
localStorage.setItem("theme", nextTheme);
```

## 结语

框架解决的是规模化问题；原生 API 解决的是对浏览器的基本理解。两者不是对立的。""",
        },
        {
            "title": "我的 2026 学习路线：少即是多",
            "category": "生活随笔",
            "tags": ["效率"],
            "cover": "/static/img/covers/cover-design.svg",
            "is_top": False,
            "days": 28,
            "views": 98,
            "summary": "从“什么都想学”到“围绕一个作品持续迭代”，这是我今年做的最有效的减法。",
            "content": """## 曾经的清单

Python、Java、Go、前端框架、算法、数据库、云原生……清单越来越长，完成率却越来越低。每学一点就换方向，最后什么都没留下。

## 今年的三个原则

1. **围绕一个作品学习**：把「知识小栈」做完、部署、写文档，比收藏十门课更有价值。
2. **每周只设一个主线**：其他学习都服务于这条主线。
3. **输出倒逼输入**：每两周写一篇可公开的文章，讲不清的地方就是没学会。

## 我接受的不完美

- 页面不可能一次做到设计师级别；
- 代码不可能没有重复；
- 文档可以后续补充。

先完成一个闭环，再在真实反馈里迭代。**完成比完美更接近成长。**

## 给下学期的一句话

把时间花在能留下痕迹的事情上：一个可以访问的网站、一份能讲清楚的文档、一次完整的复盘。""",
        },
        {
            "title": "Flask-SQLAlchemy 分页与 N+1 查询排查",
            "category": "后端之道",
            "tags": ["Flask", "MySQL", "Python"],
            "cover": "/static/img/covers/cover-data.svg",
            "is_top": False,
            "days": 35,
            "views": 121,
            "summary": "列表页突然变慢？从一条 SQL 日志开始，定位 N+1，再用 selectinload 优化。",
            "content": """## 现象

文章列表只有 6 条，却执行了 20 多次 SQL。打开 SQLAlchemy 的 echo 后，发现每条文章都单独查了一次分类和作者。

## 原因：懒加载

模板里访问 `post.category.name`、`post.author.display_name` 时，ORM 才去数据库取关联对象。列表越长，查询次数越多，这就是 N+1。

## 解决：预加载

```python
from sqlalchemy.orm import joinedload, selectinload

stmt = (
    select(Post)
    .options(
        joinedload(Post.category),
        joinedload(Post.author),
        selectinload(Post.tags),
    )
    .order_by(Post.published_at.desc())
)
```

- 多对一（分类、作者）用 `joinedload`，一次 JOIN 取回；
- 多对多（标签）用 `selectinload`，一条 IN 查询取回，避免笛卡尔积。

## 分页的正确姿势

```python
pagination = db.paginate(
    stmt,
    page=page,
    per_page=6,
    error_out=False,
)
```

`error_out=False` 让超范围页码返回空列表，而不是 404，页面体验更平滑。

## 检查清单

- 列表页是否只查了当前页？
- 关联对象是否预加载？
- 是否真的需要 `select *`？
- 慢查询是否加了合适的索引？

性能优化从观察开始，不要凭感觉改代码。""",
        },
    ]

    posts = []
    for index, spec in enumerate(post_specs):
        published_at = now - timedelta(days=spec["days"], hours=index)
        post = Post(
            title=spec["title"],
            summary=spec["summary"],
            content_md=spec["content"],
            content_html=render_markdown(spec["content"]),
            cover_image=spec["cover"],
            category_id=categories[spec["category"]].id,
            author_id=admin.id,
            status="published",
            is_top=spec["is_top"],
            view_count=spec["views"],
            created_at=published_at - timedelta(days=1),
            updated_at=published_at,
            published_at=published_at,
        )
        post.tags = [tags[name] for name in spec["tags"]]
        db.session.add(post)
        posts.append(post)

    draft = Post(
        title="下一站：把知识栈部署到云服务器",
        summary="部署清单草稿：Nginx、Gunicorn、HTTPS 与数据库备份。",
        content_md="""## 部署清单（草稿）

- [ ] 购买云服务器与域名
- [ ] 安装 Python 3.12、MySQL 8.0
- [ ] 配置 Gunicorn + Nginx
- [ ] 申请 HTTPS 证书
- [ ] 设置数据库每日备份

> 把部署过程写成可复现的步骤，是这篇文章的目标。""",
        content_html="",
        cover_image="/static/img/covers/cover-default.svg",
        category_id=categories["后端之道"].id,
        author_id=admin.id,
        status="draft",
        is_top=False,
        view_count=0,
        created_at=now - timedelta(days=1),
        updated_at=now,
        published_at=None,
    )
    draft.content_html = render_markdown(draft.content_md)
    draft.tags = [tags["Flask"], tags["MySQL"]]
    db.session.add(draft)
    db.session.flush()

    # 评论
    comments = [
        Comment(
            post_id=posts[0].id,
            user_id=reader.id,
            content="三层结构很受启发！我准备把收藏夹里的链接按「入口—加工—出口」重新整理一遍。",
            status="approved",
            created_at=now - timedelta(days=1, hours=3),
            audited_at=now - timedelta(days=1, hours=2),
            audited_by=admin.id,
        ),
        Comment(
            post_id=posts[1].id,
            guest_name="林间",
            guest_email="lin@example.com",
            content="应用工厂这段讲得很清楚，尤其是测试用独立数据库的部分。请问蓝图之间共享工具函数放在哪里比较合适？",
            status="approved",
            created_at=now - timedelta(days=4),
            audited_at=now - timedelta(days=4),
            audited_by=admin.id,
        ),
        Comment(
            post_id=posts[1].id,
            guest_name="阿岚",
            guest_email="alan@example.com",
            content="刚好在做 Flask 课设，这篇先收藏了，等我把项目跑起来再来交流。",
            status="pending",
            created_at=now - timedelta(hours=6),
        ),
        Comment(
            post_id=posts[2].id,
            user_id=reader.id,
            content="请问 utf8mb4_0900_ai_ci 和 utf8mb4_general_ci 在中文排序上差别大吗？",
            status="pending",
            created_at=now - timedelta(hours=2),
        ),
        Comment(
            post_id=posts[3].id,
            guest_name="Momo",
            content="用变量管理颜色确实舒服，暗黑模式再也不用复制一遍样式了。",
            status="approved",
            created_at=now - timedelta(days=10),
            audited_at=now - timedelta(days=10),
            audited_by=admin.id,
        ),
    ]
    db.session.add_all(comments)

    # 收藏
    for post in posts[:3]:
        db.session.add(
            Favorite(
                user_id=reader.id,
                post_id=post.id,
                created_at=now - timedelta(days=3),
            )
        )

    # 近 7 天浏览明细：让数据看板有真实形状
    for day_offset in range(6, -1, -1):
        day_base = now - timedelta(days=day_offset)
        daily_count = [8, 14, 11, 23, 18, 27, 19][6 - day_offset]
        for _ in range(daily_count):
            post = rng.choice(posts)
            db.session.add(
                PostView(
                    post_id=post.id,
                    visitor_key=f"seed-{rng.randint(1000, 9999)}",
                    viewed_at=day_base.replace(
                        hour=rng.randint(8, 22),
                        minute=rng.randint(0, 59),
                        second=0,
                        microsecond=0,
                    ),
                )
            )

    db.session.commit()
