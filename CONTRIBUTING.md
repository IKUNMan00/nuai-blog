# 贡献指南（Contributing）

感谢参与「我的知识小栈」。开始写代码前，请先阅读：

- [GitHub 协作规范](docs/06-GitHub协作规范.md)
- [需求文档](docs/01-项目需求文档.md)
- [数据库设计](docs/02-数据库设计文档.md)

## 最短流程

```bash
# 1. 同步主分支
git switch develop
git pull origin develop

# 2. 开功能分支
git switch -c feature/post-editor

# 3. 开发并自测
pytest -q

# 4. 提交（遵循 Conventional Commits）
git add .
git commit -m "feat(post): 增加 Markdown 实时预览"

# 5. 推送并开 PR
git push -u origin feature/post-editor
```

## 提交前检查

- [ ] `pytest -q` 通过
- [ ] 没有提交 `.env`、`*.db`、上传图片、`__pycache__`
- [ ] 新增页面在浅色/暗黑主题下均可读
- [ ] 涉及数据库时同步 `database/schema.sql` 与文档
- [ ] PR 描述写清楚“做了什么、为什么、怎么验证”

## 代码风格

- Python 遵循 PEP 8，函数与关键逻辑使用中文注释；
- 模板缩进 2 空格，Jinja 变量使用语义化命名；
- CSS 使用设计变量，不新增孤立色值；
- JavaScript 使用 `const/let`，避免全局变量；
- 不在模板中写复杂业务逻辑，查询放到路由/模型。

## 提交信息

```text
feat(post): 增加文章置顶开关
fix(comment): 修复待审核评论公开展示
docs(readme): 补充 Docker 启动说明
```

一次提交只做一件事。禁止 `update`、`fix bug`、`123` 这类无意义信息。
