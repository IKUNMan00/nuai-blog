# 《我的知识小栈》GitHub 仓库使用流程与小组协作规范

| 项目 | 内容 |
| --- | --- |
| 仓库建议名 | `knowledge-stack` |
| 默认分支 | `main`（受保护，只接受 PR） |
| 开发分支 | `develop`（集成分支） |
| 分支模型 | 简化 Git Flow + GitHub Flow |
| 提交规范 | Conventional Commits（中文描述） |
| 评审方式 | 至少 1 人 Approve + CI 通过 |
| 合并策略 | Squash merge，保持 main 线性 |
| 配套文件 | `.github/workflows/ci.yml`、`PULL_REQUEST_TEMPLATE.md`、Issue 模板、`CONTRIBUTING.md` |

---

## 1. 仓库初始化（组长执行一次）

```bash
cd knowledge-stack
git init
git branch -M main

# 首次提交
git add .
git commit -m "chore: 初始化知识小栈项目骨架"
git remote add origin https://github.com/<org>/knowledge-stack.git
git push -u origin main

# 创建集成分支
git switch -c develop
git push -u origin develop
```

### 1.1 分支保护设置

在 GitHub → Settings → Branches：

- 保护 `main`：
  - 禁止直接 push；
  - 合并前必须通过 CI；
  - 合并前至少 1 个 Approve；
  - 要求分支与最新 `main` 同步；
  - 禁止强制推送、禁止删除。
- 保护 `develop`：
  - 禁止直接 push（或允许组长紧急修复）；
  - CI 必须通过。

### 1.2 仓库基础设置

- Description：`Flask + MySQL 个人博客/笔记管理系统 · 课程综合训练项目`
- Topics：`flask`、`mysql`、`blog`、`knowledge-management`、`course-project`
- 开启 Issues、Projects（看板）、Discussions（可选）
- Secrets 中只放 CI 所需变量，绝不放生产数据库密码
- 添加 `.gitignore`、`LICENSE`、`README.md`、`CONTRIBUTING.md`

---

## 2. 小组角色与分工

> 角色不固定，全员参与前后端、数据库全流程；以下为“主责 + 协作”模式，避免一人只做一类工作。

| 成员 | 主责模块 | 协作内容 | GitHub 角色 |
| --- | --- | --- | --- |
| 成员 A（组长） | 项目统筹、认证与权限、部署 | 需求文档、PR 评审、合并、答辩串场 | Admin / Maintainer |
| 成员 B | 文章 CRUD、分类标签、搜索 | 数据库设计、接口测试、后台页面联调 | Write |
| 成员 C | 前端设计系统、首页/列表/详情 | CSS 变量、双主题、响应式、视觉验收 | Write |
| 成员 D | 评论审核、收藏、账号中心 | 数据表、权限测试、路演演示 | Write |
| 成员 E | Markdown 编辑器、图片附件、看板 | 前端交互、上传安全、测试与录屏 | Write |

### 2.1 模块归属矩阵

| 模块 | 主责 | 备份 / 评审 |
| --- | --- | --- |
| `auth.py` / 权限 | A | B |
| `main.py` 列表与搜索 | B | D |
| `main.py` 详情与评论 | D | B |
| `admin.py` 文章/分类/标签 | B | A |
| `admin.py` 评论/附件 | D | E |
| `admin.py` 看板 | E | B |
| `models.py` / SQL | B | A |
| `style.css` / 模板 | C | E |
| `app.js` / `editor.js` | E | C |
| 测试 / CI / 部署 | A | 全员 |
| 文档 / PPT / 录屏 | 全员 | A 统稿 |

### 2.2 每周协作节奏

| 时间 | 事项 | 产出 |
| --- | --- | --- |
| 周一 20:00 | 站会 30 分钟 | 本周目标、Issue 拆分、认领 |
| 周三 | 中期同步 | 阻塞问题、接口变更、联调 |
| 周五 | 代码评审 + 合并 | PR 合并到 develop，更新看板 |
| 周日 | 周复盘 | 完成/未完成、下周计划、文档更新 |

---

## 3. 分支模型

```text
main        ●────────●────────●────────●   （只接受 PR，可发布）
              ╲      ╱ ╲      ╱
develop        ●────●───●────●───●────●     （集成分支）
                 ╲  ╱     ╲  ╱
feature/*         ●─●       ●─●             （功能分支，短生命周期）
```

| 分支 | 命名 | 来源 | 合并到 | 生命周期 |
| --- | --- | --- | --- | --- |
| `main` | `main` | — | — | 长期，随时可演示 |
| `develop` | `develop` | `main` | `main`（发布时） | 长期 |
| 功能 | `feature/<scope>-<short>` | `develop` | `develop` | 1–5 天 |
| 修复 | `fix/<scope>-<short>` | `develop` | `develop` | 1–2 天 |
| 文档 | `docs/<topic>` | `develop` | `develop` | 1–3 天 |
| 紧急修复 | `hotfix/<topic>` | `main` | `main` + `develop` | 当天 |
| 发布 | `release/vX.Y.Z` | `develop` | `main` + `develop` | 1 天 |

### 3.1 命名示例

```text
feature/auth-login
feature/post-editor
feature/comment-moderation
feature/admin-dashboard
fix/comment-pending-leak
fix/mysql-charset
docs/db-design
style/dark-theme
test/upload-validation
```

规则：

- 全小写，短横线分隔；
- 不超过 40 字符；
- 一个分支只做一件事；
- 合并后删除远端分支。

---

## 4. 日常开发流程

### 4.1 开始新功能

```bash
# 1. 同步 develop
git switch develop
git pull origin develop

# 2. 创建分支
git switch -c feature/post-editor

# 3. 开发，小步提交
git add app/templates/admin/post_form.html app/static/js/editor.js
git commit -m "feat(post): 增加 Markdown 实时预览"

# 4. 持续同步 develop，减少最终冲突
git fetch origin
git rebase origin/develop

# 5. 推送
git push -u origin feature/post-editor
```

### 4.2 提交前自检

```bash
pytest -q
git status
git diff --stat
git diff
```

检查：

- 没有 `.env`、`*.db`、`app/static/uploads/*`、`__pycache__`；
- 没有调试用的 `print`、`console.log`、临时账号；
- 没有把 `SECRET_KEY` 写死；
- 新增页面已看浅色/暗黑/手机；
- 数据库变更同步了模型、SQL、文档。

### 4.3 发起 PR

- 标题：`[feat] 增加 Markdown 实时预览` 或 `feat(post): ...`；
- 描述按模板填写：做了什么、关联 Issue、变更类型、自测、截图；
- 指定 1–2 位 Reviewer；
- 关联 Issue：`Closes #12`；
- 不要一上来就 @ 全组，先自己跑通 CI。

### 4.4 代码评审

Reviewer 重点看：

| 维度 | 检查项 |
| --- | --- |
| 正确性 | 边界条件、空数据、权限、事务 |
| 安全 | SQL 注入、XSS、CSRF、越权、上传 |
| 可维护性 | 函数是否过长、命名是否清晰、是否重复 |
| 一致性 | 是否符合现有分层、CSS token、模板结构 |
| 测试 | 是否有对应测试；测试是否真的断言 |
| 文档 | 接口/数据库/README 是否同步 |

评论用语：

- 阻塞问题：`[must] 这里读者可以进入后台，需要加角色校验。`
- 建议：`[nit] 这个查询可以复用 POST_LOADS，减少重复。`
- 提问：`[q] 为什么这里用 20 秒而不是 60 秒？`

### 4.5 合并

- 至少 1 个 Approve；
- CI 绿色；
- 无冲突；
- 使用 **Squash and merge**；
- Squash 提交信息遵循 Conventional Commits；
- 合并后删除功能分支；
- 更新 Project 看板状态。

### 4.6 发布

```bash
git switch develop
git pull
git switch -c release/v1.0.0
# 更新版本号、CHANGELOG、最后回归
git commit -m "chore(release): 发布 v1.0.0"
git push -u origin release/v1.0.0
# 开 PR 到 main，评审通过后合并
git switch main
git pull
git tag -a v1.0.0 -m "课程项目 v1.0.0"
git push origin v1.0.0
# 再合并回 develop
```

---

## 5. 提交规范（Conventional Commits）

### 5.1 格式

```text
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

- 一行不超过 72 个字符；
- 使用中文描述“做了什么”，不要写“更新”“修改”；
- 一次提交只做一件事；
- 不修改历史提交（除非组长明确要求）。

### 5.2 type

| type | 含义 | 示例 |
| --- | --- | --- |
| `feat` | 新功能 | `feat(post): 增加文章置顶开关` |
| `fix` | 修复缺陷 | `fix(comment): 修复待审核评论公开展示` |
| `docs` | 文档 | `docs(db): 补充索引设计说明` |
| `style` | 样式/格式 | `style(ui): 统一暗黑模式卡片边框` |
| `refactor` | 重构（不改行为） | `refactor(admin): 抽离文章表单校验` |
| `test` | 测试 | `test(auth): 增加读者越权用例` |
| `chore` | 构建/依赖/配置 | `chore(deps): 升级 Flask 至 3.1` |
| `perf` | 性能 | `perf(post): 预加载分类与标签` |
| `ci` | CI 配置 | `ci: 增加 pytest 工作流` |

### 5.3 scope

`auth`、`post`、`comment`、`favorite`、`category`、`tag`、`upload`、`dashboard`、`ui`、`db`、`docs`、`deploy`、`test`、`deps`。

### 5.4 示例提交序列

```text
chore: 初始化 Flask 项目骨架
feat(auth): 实现博主登录与读者注册
feat(post): 完成文章列表与详情页
feat(admin): 增加文章创建与编辑
feat(category): 增加分类 CRUD
feat(tag): 增加标签多选与新建
feat(search): 支持标题与正文关键词检索
feat(comment): 实现游客评论与审核队列
feat(favorite): 增加收藏与我的收藏页
feat(editor): 增加 Markdown 实时预览
feat(upload): 增加图片校验与附件库
feat(dashboard): 增加 7 日访问与分类分布
style(ui): 完成浅色/暗黑双主题
fix(comment): 未审核评论不再出现在前台
fix(auth): 修复开放重定向风险
test(app): 覆盖 13 个核心流程
docs(db): 完成数据库设计文档
docs(readme): 补充 Docker 启动说明
ci: 增加 GitHub Actions 测试
chore(release): 发布 v1.0.0
```

> 上述是建议提交序列，不要求逐条照抄。课堂检查更看重“提交是否真实、粒度是否合理、信息是否清楚”。

---

## 6. Issue 管理

### 6.1 Issue 类型

| 类型 | 模板 | 用途 |
| --- | --- | --- |
| Bug | `bug_report.md` | 可复现缺陷 |
| Feature | `feature_request.md` | 功能任务 / 验收标准 |
| Task | 手动 | 文档、部署、设计等杂项 |

### 6.2 Issue 标题

```text
[Bug] 读者可以直接访问 /admin/dashboard
[Feature] 文章编辑支持实时 Markdown 预览
[Docs] 补充数据库索引说明
```

### 6.3 Issue 生命周期

```text
Open（待认领）
  → In Progress（Projects 看板）
  → In Review（关联 PR）
  → Done（PR 合并后自动关闭）
```

要求：

- 一个 Issue 对应一个可验收结果；
- 描述里写清楚复现步骤/验收标准；
- 关联 PR 用 `Closes #12`；
- 不在 Issue 里讨论无关话题。

---

## 7. Project 看板

建议列：

| 列 | 含义 |
| --- | --- |
| Backlog | 已识别但未排期 |
| Todo | 本周要做 |
| In Progress | 进行中（限制每人 1–2 项） |
| In Review | 等 PR 评审 |
| Done | 已合并 |

每张卡片：

- 标题 + 负责人 + 截止日期；
- 关联 Issue / PR；
- 验收标准；
- 阻塞原因（如有）。

---

## 8. 冲突处理

### 8.1 预防

- 小步提交，频繁同步 `develop`；
- 按模块拆文件，避免多人同时改同一大文件；
- CSS 新增样式集中在各自区块，减少同位置冲突；
- 数据库变更先沟通，再改模型/SQL/文档；
- 模板宏与公共组件由 C 统一维护。

### 8.2 解决

```bash
git fetch origin
git rebase origin/develop
# 解决冲突
git add <冲突文件>
git rebase --continue
pytest -q
git push --force-with-lease
```

原则：

- 冲突不是“选一边”，要理解两边意图；
- 数据模型冲突以数据库设计文档为准，先对齐再改；
- 解决后必须重新跑测试；
- 不直接 `git checkout --theirs .` 全量覆盖。

### 8.3 紧急回滚

```bash
# 找到坏提交
git log --oneline
# 反转某次提交（生成新提交，安全）
git revert <commit>
git push
```

不要在共享分支上 `git reset --hard` 后强推。

---

## 9. 代码评审清单

### 9.1 后端

- [ ] 路由是否做了登录/角色校验？
- [ ] 表单字段是否服务端校验？
- [ ] 查询是否参数化？是否有 N+1？
- [ ] 写操作是否在同一事务？
- [ ] 删除是否正确处理关联数据？
- [ ] 错误提示是否对用户友好且不泄露敏感信息？
- [ ] 是否补充了测试？

### 9.2 前端

- [ ] 是否复用设计变量与组件？
- [ ] 浅色/暗黑是否都可读？
- [ ] 手机宽度是否溢出？
- [ ] 表单是否有 label 与错误反馈？
- [ ] 图片是否有 alt / lazy？
- [ ] 交互是否可键盘完成？
- [ ] 是否引入外部 CDN？

### 9.3 文档 / 部署

- [ ] README 命令是否可复制运行？
- [ ] `.env.example` 是否同步？
- [ ] Docker 是否仍能启动？
- [ ] 数据库变更是否同步三处（模型 / SQL / 文档）？
- [ ] 是否误提交生成文件或密钥？

---

## 10. 小组协作约定

1. **每日一句话同步**：昨天做了什么、今天做什么、有无阻塞；
2. **接口先对齐**：路由、字段、状态码确定后再并行开发；
3. **公共组件集中改**：`base.html`、`_macros.html`、`style.css` 由 C 主责，其他人提 PR；
4. **不跨模块直接改**：需要改别人的文件先在群里说明，避免冲突；
5. **评审不针对人**：对事不对人，使用 `[must]/[nit]/[q]` 标注；
6. **演示分支随时可跑**：`main` 保持可运行，不把半成品合进去；
7. **文档跟着代码走**：功能合并时同步 README/接口/数据库文档；
8. **保留真实记录**：不伪造提交时间、不代刷贡献，课堂检查以真实协作为准。

---

## 11. 常见问题

**Q：可以直接在 main 上改一个小错吗？**
不建议。即使一行，也走 `fix/...` 分支 + PR，保证 CI 与评审记录完整。紧急情况由组长操作并补 PR。

**Q：功能分支落后 develop 很多怎么办？**
用 `git rebase origin/develop`，解决冲突后 `--force-with-lease` 推送。不要用普通 `--force`。

**Q：两个人同时改了 `style.css` 怎么办？**
先沟通；C 负责合并，保留双方意图；合并后统一跑视觉检查。后续尽量按区块拆分，减少同位置修改。

**Q：数据库改了字段，要改哪些地方？**
至少四处：`app/models.py`、`database/schema.sql`、`docs/02-数据库设计文档.md`、相关测试/种子数据。缺一不可。

**Q：CI 挂了但本地能过？**
检查 Python 版本、依赖版本、环境变量、SQLite/MySQL 差异、是否漏提交文件。按 CI 日志修，不要直接跳过测试。

**Q：需要把 `.env` 提交给老师吗？**
不提交。提交 `.env.example` 和 README 说明；答辩时演示本机配置即可。

---

## 12. 课堂检查材料对应

| 检查项 | 仓库位置 |
| --- | --- |
| 提交记录与分支 | GitHub Insights / Network |
| 提交规范 | `git log --oneline --graph` |
| PR 与评审 | Pull Requests 页面 |
| Issue 与看板 | Issues / Projects |
| CI | Actions 页面 |
| 协作文档 | 本文 + `CONTRIBUTING.md` |
| 代码规范 | `app/` + `tests/` |
| 部署 | `Dockerfile`、`docker-compose.yml`、README |
| 演示 | `docs/07`、`docs/08`、`deliverables/` |

---

> 协作规范的目的不是增加流程，而是让五个人并行开发时**少冲突、可追溯、能回滚**。所有规则服务于“按时交付一个能跑、能讲清楚的项目”。
