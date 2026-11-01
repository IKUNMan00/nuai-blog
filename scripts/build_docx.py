"""生成《我的知识小栈》课程个人总结模板 DOCX。"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "我的知识小栈-课程个人总结模板.docx"

GREEN = RGBColor(0x1F, 0x6F, 0x5C)
DARK = RGBColor(0x12, 0x3F, 0x34)
TERRA = RGBColor(0xC9, 0x6F, 0x3B)
INK = RGBColor(0x1C, 0x2A, 0x22)
SOFT = RGBColor(0x45, 0x56, 0x4B)
MUTED = RGBColor(0x6D, 0x7B, 0x71)
WHITE = RGBColor(0xFF, 0xFD, 0xF8)
LIGHT = "E5F0EA"
PALE = "F6F4EE"
PEACH = "F6E5D8"

FONT_BODY = "Microsoft YaHei"
FONT_SERIF = "SimSun"
FONT_MONO = "Consolas"


def set_run_font(run, name=FONT_BODY, size=10.5, color=INK, bold=False, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)


def shade_cell(cell, fill):
    if isinstance(fill, RGBColor):
        fill = str(fill)
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")
    tc_pr.append(shd)


def set_cell_margins(cell, top=0.12, bottom=0.12, left=0.18, right=0.18):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(int(value * 567)))
        node.set(qn("w:type"), "dxa")


def keep_row_together(table):
    """避免提示框/表格行被分页切成一条残片。"""
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)


def set_cell_borders(cell, color="D9D5C9", size=4):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:color"), color)
        borders.append(element)
    tc_pr.append(borders)


def page_break(doc):
    doc.add_page_break()


def add_header_footer(section):
    header = section.header
    p = header.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("我的知识小栈 · 课程个人总结")
    set_run_font(run, FONT_MONO, 8, GREEN, True)
    p.add_run("\t\t")
    run = p.add_run("课程综合训练项目 · 2026")
    set_run_font(run, FONT_MONO, 8, MUTED)
    # 页脚页码
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = fp.add_run("— ")
    set_run_font(run, FONT_BODY, 9, MUTED)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run = fp.add_run()
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    run = fp.add_run(" —")
    set_run_font(run, FONT_BODY, 9, MUTED)


def add_bottom_border(paragraph, color="1F6F5C", size=8):
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def heading(doc, text, number=""):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.keep_with_next = True
    if number:
        run = p.add_run(number + "  ")
        set_run_font(run, FONT_SERIF, 17, TERRA, True)
    run = p.add_run(text)
    set_run_font(run, FONT_SERIF, 17, GREEN, True)
    add_bottom_border(p)
    return p


def subheading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, FONT_BODY, 11.5, INK, True)
    return p


def rich_para(doc, text, size=10.5, color=INK, italic=False, first_line=True, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.55
    p.paragraph_format.space_after = Pt(space_after)
    if first_line:
        p.paragraph_format.first_line_indent = Cm(0.74)
    parts = re.split(r"(【[^】]+】)", text)
    for part in parts:
        if not part:
            continue
        run = p.add_run(part)
        if part.startswith("【"):
            set_run_font(run, FONT_BODY, size, TERRA, True, italic)
        else:
            set_run_font(run, FONT_BODY, size, color, False, italic)
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.9)
    parts = re.split(r"(【[^】]+】)", text)
    for part in parts:
        if not part:
            continue
        run = p.add_run(part)
        set_run_font(run, FONT_BODY, size, TERRA if part.startswith("【") else SOFT, part.startswith("【"))
    return p


def tip_box(doc, text, fill=LIGHT, border="C7DFD4", label="填写提示"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    cell = table.cell(0, 0)
    shade_cell(cell, fill)
    set_cell_borders(cell, border, 6)
    set_cell_margins(cell, 0.16, 0.16, 0.24, 0.24)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.35
    run = p.add_run(f"{label}  ")
    set_run_font(run, FONT_MONO, 8, GREEN, True)
    run = p.add_run(text)
    set_run_font(run, FONT_BODY, 9, SOFT, False, True)
    keep_row_together(table)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.line_spacing = 0.6
    return table


def example_box(doc, text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    shade_cell(cell, "FBFAF6")
    set_cell_borders(cell, "E3DFD3", 4)
    set_cell_margins(cell, 0.16, 0.16, 0.24, 0.24)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.45
    run = p.add_run("参考示例（请用自己的话重写）  ")
    set_run_font(run, FONT_MONO, 8, TERRA, True)
    run = p.add_run(text)
    set_run_font(run, FONT_BODY, 9.2, MUTED, False, True)
    keep_row_together(table)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.line_spacing = 0.6


def data_table(doc, headers, rows, widths=None, header_fill=DARK):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    header_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        cell = header_cells[i]
        shade_cell(cell, header_fill)
        set_cell_margins(cell, 0.12, 0.12, 0.16, 0.16)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        set_run_font(run, FONT_BODY, 9, WHITE, True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            set_cell_borders(cell, "D9D5C9", 4)
            set_cell_margins(cell, 0.12, 0.12, 0.16, 0.16)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.3
            parts = re.split(r"(【[^】]+】)", str(value))
            for part in parts:
                if not part:
                    continue
                run = p.add_run(part)
                set_run_font(
                    run, FONT_BODY, 9,
                    TERRA if part.startswith("【") else SOFT,
                    part.startswith("【"),
                )
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)
    keep_row_together(table)
    return table


# =====================================================================
doc = Document()
section = doc.sections[0]
section.page_height = Cm(29.7)
section.page_width = Cm(21.0)
section.top_margin = Cm(2.2)
section.bottom_margin = Cm(2.0)
section.left_margin = Cm(2.4)
section.right_margin = Cm(2.2)
section.header_distance = Cm(1.0)
section.footer_distance = Cm(0.9)
add_header_footer(section)

normal = doc.styles["Normal"]
normal.font.name = FONT_BODY
normal.font.size = Pt(10.5)
normal.font.color.rgb = INK
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_BODY)

# ---------------- 封面 ----------------
cover = doc.add_table(rows=1, cols=1)
cover.alignment = WD_TABLE_ALIGNMENT.CENTER
cell = cover.cell(0, 0)
shade_cell(cell, "123F34")
set_cell_margins(cell, 0.5, 0.55, 0.7, 0.7)
p = cell.paragraphs[0]
p.paragraph_format.space_after = Pt(18)
run = p.add_run("COURSE PROJECT  ·  2026")
set_run_font(run, FONT_MONO, 8.5, RGBColor(0x9F, 0xBE, 0xAD), True)
p2 = cell.add_paragraph()
p2.paragraph_format.space_after = Pt(6)
run = p2.add_run("我的知识小栈")
set_run_font(run, FONT_SERIF, 28, RGBColor(0xFF, 0xFD, 0xF8), True)
p3 = cell.add_paragraph()
p3.paragraph_format.space_after = Pt(18)
run = p3.add_run("课程个人总结")
set_run_font(run, FONT_SERIF, 18, RGBColor(0xF6, 0xE5, 0xD8), False)
p4 = cell.add_paragraph()
p4.paragraph_format.space_after = Pt(0)
run = p4.add_run("把零散的知识，收进一座会生长的小栈。")
set_run_font(run, FONT_SERIF, 10.5, RGBColor(0xB9, 0xCD, 0xC2), False, True)

space = doc.add_paragraph()
space.paragraph_format.space_after = Pt(16)

info = data_table(
    doc,
    ["项目", "内容", "项目", "内容"],
    [
        ["课程名称", "【软件工程 / Web 开发 / 数据库课程】", "小组名称", "【第 X 组】"],
        ["项目名称", "我的知识小栈——个人博客 / 笔记管理系统", "小组角色", "【后端 / 前端 / 数据库 / 测试 / 文档】"],
        ["学生姓名", "【姓名】", "学号", "【学号】"],
        ["专业班级", "【专业 + 班级】", "提交日期", "【2026 年 X 月 X 日】"],
    ],
    widths=[2.4, 6.1, 2.4, 5.3],
)
for row in info.rows[1:]:
    for idx in (0, 2):
        shade_cell(row.cells[idx], PALE)

tip_box(
    doc,
    "本文档为个人独立提交模板。请删除所有【】占位符与灰色提示，结合自己的真实工作重写；"
    "示例段落只用于说明写法，不能直接复制。建议 1500–2500 字。",
    fill=PEACH,
    border="E8CBB8",
    label="使用说明",
)

doc.add_paragraph()
sign = doc.add_paragraph()
sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = sign.add_run("学生签名：__________________          日期：______年____月____日")
set_run_font(run, FONT_BODY, 10, MUTED)

page_break(doc)

# ---------------- 一、课程学习回顾 ----------------
heading(doc, "课程学习回顾", "一")
subheading(doc, "1.1 本学期我学到的核心知识")
rich_para(
    doc,
    "【用 3–5 句话概括本学期的变化。建议从“以前只会写单文件脚本，到现在能完成一个分层 Web 项目”"
    "这样的前后对比切入，写出具体知识点，不要只写“收获很大”。】",
)
tip_box(
    doc,
    "可以围绕 Web 请求流程、数据库设计、分层开发、Git 协作、测试与部署来写。"
    "每个知识点最好对应一个项目中的具体位置。",
)
example_box(
    doc,
    "本学期课程从 Web 基础、数据库设计讲到后端开发和部署。我最大的变化是：以前写代码只追求“能跑”，"
    "现在会先想清楚数据表怎么设计、接口边界在哪里、权限和异常怎么处理。课程中的 MVC、SQL、HTTP、Git 等知识，"
    "最终都在这个项目里串了起来。",
)

subheading(doc, "1.2 与项目最相关的三个知识点")
data_table(
    doc,
    ["知识点", "课程中的理解", "在项目中的落地"],
    [
        ["【如：关系数据库设计】", "【范式、主外键、索引】", "【设计 9 张表、联合主键、组合索引】"],
        ["【如：HTTP 与会话】", "【请求/响应、Cookie、Session】", "【Flask-Login 登录、CSRF、权限】"],
        ["【如：前端布局】", "【盒模型、Flex/Grid】", "【响应式页面、CSS 变量双主题】"],
    ],
    widths=[3.6, 5.2, 7.4],
)
tip_box(doc, "不要把课程概念抄一遍，重点写“课程里怎么理解 → 项目里怎么用 → 遇到了什么差异”。")

# ---------------- 二、项目工作 ----------------
heading(doc, "我在项目中承担的工作", "二")
subheading(doc, "2.1 角色与模块")
rich_para(
    doc,
    "我在组内主要负责【文章模块的后端接口与后台页面】，同时参与了【数据库设计评审、评论审核联调、"
    "测试用例补充】。主要负责的文件包括【app/main.py、app/admin.py 中的文章部分、"
    "templates/admin/post_form.html】。",
)
subheading(doc, "2.2 具体工作清单")
for item in [
    "【功能 1：实现文章列表分页、搜索、分类/标签组合筛选】",
    "【功能 2：实现文章新建/编辑/删除、草稿与发布状态】",
    "【功能 3：参与 9 张表设计，编写 database/schema.sql】",
    "【协作 1：评审评论审核 PR，补充越权测试】",
    "【文档 1：撰写数据库设计文档第 3–5 节】",
    "【演示 1：负责录屏中的后台流程与 PPT 第 8 页】",
]:
    bullet(doc, item)

subheading(doc, "2.3 可验证的贡献")
data_table(
    doc,
    ["类型", "证据（填写真实链接 / 编号 / 截图说明）"],
    [
        ["代码提交", "【GitHub 用户名 / 提交范围，如 feat(post): ... 共 12 次提交】"],
        ["Pull Request", "【PR 编号与标题，如 #18 文章编辑器】"],
        ["Issue", "【认领/关闭的 Issue，如 #7 搜索组合筛选】"],
        ["文档", "【负责的章节】"],
        ["测试", "【新增的测试用例，如 test_create_edit_and_delete_post】"],
        ["演示", "【录屏时间段 / PPT 页码】"],
    ],
    widths=[3.3, 13.0],
)
tip_box(doc, "建议在附录附 1–2 张截图：GitHub 提交记录、PR 评审、自己负责的页面。截图需清晰并打码敏感信息。")

# ---------------- 三、技术收获 ----------------
heading(doc, "技术收获", "三")
subheading(doc, "3.1 后端：从“写路由”到“分层”")
rich_para(
    doc,
    "【写一个具体技术点，不要泛泛而谈。建议从应用工厂、蓝图、ORM、权限、事务中选一个，"
    "写清楚“以前怎么做 → 现在怎么做 → 为什么”。】",
)
example_box(
    doc,
    "以前我把所有路由写在一个 app.py 里，变量和数据库连接都是全局的。这个项目第一次用应用工厂和蓝图："
    "create_app() 负责装配，main/auth/admin/api 各自管一块。最开始我不理解为什么要多这一层，"
    "直到写测试时发现可以给测试单独注入 SQLite 配置，才意识到它的价值。",
)

subheading(doc, "3.2 数据库：从“能存”到“存得对”")
rich_para(
    doc,
    "【写一个具体设计取舍，如联合主键、外键级联、索引、冗余字段。说明为什么这样设计、代价是什么。】",
)
example_box(
    doc,
    "收藏表最初我加了自增主键，后来发现同一用户可能重复收藏同一篇文章。改成 (user_id, post_id) 联合主键后，"
    "重复插入会直接被数据库拒绝。另一个取舍是 posts.view_count：它和 post_views 明细表看起来冗余，"
    "但热门排序需要汇总值，每次都 COUNT 会很慢，所以保留了这个冗余字段。",
)

subheading(doc, "3.3 前端：从“堆样式”到“设计系统”")
rich_para(
    doc,
    "【写 CSS 变量、响应式、可访问性、原生 JS 中的一点。最好写出“维护成本”的变化。】",
)
subheading(doc, "3.4 安全：从“没见过”到“会防御”")
rich_para(
    doc,
    "【写 XSS、CSRF、越权、上传中的一点。说明攻击面、你的防御措施、如何验证。】",
)
example_box(
    doc,
    "做 Markdown 预览时，我一开始直接 innerHTML = marked(...)，后来意识到这等于允许用户注入脚本。"
    "改成后端 Python-Markdown 渲染后再用 bleach 白名单过滤，并且只对文章正文使用 |safe。"
    "我们还补了一个测试，输入 <script> 后断言输出里没有脚本标签。",
)

# ---------------- 四、团队协作 ----------------
heading(doc, "团队协作与 GitHub 使用", "四")
subheading(doc, "4.1 我在协作中的具体做法")
rich_para(
    doc,
    "【写分支、提交、PR、评审、沟通中的真实经历。不要只写“我们用了 Git”，要写你具体做了什么、"
    "被指出什么问题、如何修改。】",
)
example_box(
    doc,
    "我负责的功能在 feature/post-editor 分支开发，完成后向 develop 发 PR。第一次 PR 被 reviewer 指出两个问题："
    "图片上传没有校验真实格式、编辑器预览接口没有限制登录。我补了 Pillow 校验和角色判断，并加了测试，"
    "第二次才通过。这个过程让我意识到 PR 不是走形式，reviewer 真的会看到自己忽略的边界。",
)

subheading(doc, "4.2 我遇到的协作问题与解决")
data_table(
    doc,
    ["问题", "我的处理", "结果"],
    [
        ["【两个人同时改 style.css 冲突】", "【先沟通，按区块合并，统一跑视觉检查】", "【保留双方样式，无回归】"],
        ["【数据库字段改了但文档没同步】", "【在 PR 清单中加入“三处同步”检查】", "【后续未再遗漏】"],
        ["【合并后测试挂了】", "【看 CI 日志，发现 SQLite 自增差异】", "【用 with_variant 修复】"],
    ],
    widths=[5.2, 7.2, 4.0],
)
subheading(doc, "4.3 我对“规范”的理解")
rich_para(
    doc,
    "【一句话即可。例如：规范不是为了限制人，而是让五个人并行时少踩坑；提交信息写清楚，"
    "未来回滚时才知道自己在回滚什么。】",
)

# ---------------- 五、问题与解决 ----------------
heading(doc, "遇到的问题与解决过程", "五")
rich_para(
    doc,
    "【选 1–2 个真实问题，写清楚“现象 → 排查 → 原因 → 解决 → 验证”。不要只写“百度了一下就好了”。】",
)
subheading(doc, "问题 1：【例如：文章列表查询出现 N+1】")
for label, text in [
    ("现象", "【列表只有 6 篇文章，却执行了 20 多条 SQL】"),
    ("排查", "【打开 SQLAlchemy echo，发现每条文章都单独查分类和作者】"),
    ("原因", "【模板访问 post.category.name 时触发懒加载】"),
    ("解决", "【列表查询加 joinedload(Post.category)、joinedload(Post.author)、selectinload(Post.tags)】"),
    ("验证", "【SQL 数量下降，页面渲染正常，测试通过】"),
]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(f"{label}：")
    set_run_font(run, FONT_BODY, 10.5, GREEN, True)
    run = p.add_run(text)
    set_run_font(run, FONT_BODY, 10.5, TERRA if text.startswith("【") else SOFT, text.startswith("【"))

subheading(doc, "问题 2：【例如：MySQL 中文乱码 / emoji 报错】")
for label in ["现象", "排查", "原因", "解决", "验证"]:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(f"{label}：")
    set_run_font(run, FONT_BODY, 10.5, GREEN, True)
    run = p.add_run("【填写】")
    set_run_font(run, FONT_BODY, 10.5, TERRA, True)

# ---------------- 六、不足与改进 ----------------
heading(doc, "不足与改进", "六")
subheading(doc, "6.1 项目层面的不足")
for item in [
    "【搜索仍是 LIKE，数据量大时性能不足】",
    "【单博主模型，没有多作者协作】",
    "【图片存本地，没有对象存储】",
    "【评论没有多级回复和邮件通知】",
]:
    bullet(doc, item)

subheading(doc, "6.2 个人层面的不足")
rich_para(
    doc,
    "【诚实写 2–3 点，不要写“我最大的不足是太追求完美”。建议写具体行为及其后果。】",
)
example_box(
    doc,
    "第一，我在前期花太多时间调视觉效果，导致后端联调开始得晚；第二，我写测试时只覆盖了正常流程，"
    "越权和异常输入是 reviewer 提醒后才补的；第三，我对 MySQL 索引的理解还停留在“加索引会更快”，"
    "没有实际用 EXPLAIN 分析过执行计划。",
)

subheading(doc, "6.3 下一步计划")
for item in [
    "【短期：补全文搜索 / 用 EXPLAIN 优化一条慢查询】",
    "【中期：学习 Docker 部署与 Nginx 配置】",
    "【长期：把这个项目继续维护，作为个人作品集】",
]:
    bullet(doc, item)

# ---------------- 七、课程建议 ----------------
heading(doc, "课程建议与反馈", "七")
rich_para(
    doc,
    "【可选，写 2–3 条具体建议，不要空泛。例如：希望增加一次代码评审示范；"
    "希望每组每周提交一次可运行版本，避免最后一周集中联调。】",
)

# ---------------- 八、结语 ----------------
heading(doc, "结语", "八")
rich_para(
    doc,
    "【用 3–5 句话收束。可以回到“知识小栈”的主题：这个项目让你第一次完整经历需求、设计、开发、"
    "测试、部署；最重要的收获不是某个框架，而是遇到问题时如何拆解、验证和记录。】",
)
example_box(
    doc,
    "这个项目让我第一次完整经历了一个软件从需求、设计、开发、测试到部署的过程。最重要的收获不是学会了某个框架，"
    "而是知道了遇到问题时应该怎样拆解、验证和记录。就像小栈的名字一样，知识不是收藏，而是写下来、用起来、再传下去。",
)

# ---------------- 九、自评 ----------------
heading(doc, "自评表", "九")
rich_para(doc, "【按课程要求填写；如不需要可删除本节。】", first_line=False)
data_table(
    doc,
    ["维度", "分值", "自评", "说明"],
    [
        ["课程知识掌握", "20", "【】", "【如：能独立完成 Flask + MySQL 项目】"],
        ["项目完成度", "25", "【】", "【如：主责模块全部完成，扩展参与 2 项】"],
        ["代码质量", "15", "【】", "【如：分层清晰，有注释和测试】"],
        ["团队协作", "20", "【】", "【如：按时提交，参与评审】"],
        ["文档与表达", "10", "【】", "【如：负责数据库文档与路演】"],
        ["学习态度", "10", "【】", "【如：遇到问题主动查资料】"],
        ["合计", "100", "【】", ""],
    ],
    widths=[4.0, 2.0, 2.0, 8.3],
)
doc.add_paragraph()

subheading(doc, "个人贡献占比说明（如课程要求）")
data_table(
    doc,
    ["模块", "我的贡献占比", "说明"],
    [
        ["【模块 1】", "【%】", "【具体工作】"],
        ["【模块 2】", "【%】", "【具体工作】"],
        ["文档 / 演示", "【%】", "【具体工作】"],
    ],
    widths=[4.0, 3.0, 9.3],
)

# ---------------- 十、附录 ----------------
heading(doc, "附录（可选）", "十")
for item in [
    "GitHub 个人主页 / 仓库链接：【】",
    "代表性 PR：【链接】",
    "负责页面截图：【插入】",
    "测试运行结果截图：【插入】",
    "录屏链接：【】",
]:
    bullet(doc, item)

doc.add_paragraph()
tip_box(
    doc,
    "提交前检查：个人信息完整；工作清单与 GitHub 对得上；至少写了 1 个具体技术问题与解决过程；"
    "不足部分真实具体；字数 1500–2500；没有直接复制组员内容；截图已打码敏感信息。",
    fill=PEACH,
    border="E8CBB8",
    label="检查清单",
)

doc.core_properties.title = "我的知识小栈 · 课程个人总结模板"
doc.core_properties.subject = "高校软件课程综合训练项目个人总结"
doc.core_properties.author = "我的知识小栈课程项目组"
doc.core_properties.keywords = "课程总结, Flask, MySQL, 个人博客, 知识管理"
doc.core_properties.comments = "模板中的【】为需要替换的个人信息。"

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(f"saved: {OUT}")
