"""生成《我的知识小栈》课程路演 PPT。

运行（使用工作区自带 Python 依赖）：
    python scripts/build_pptx.py

输出：deliverables/我的知识小栈-小组路演.pptx
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "我的知识小栈-小组路演.pptx"
ASSETS = ROOT / "deliverables" / "_ppt_assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# ---------- 设计 token ----------
CREAM = RGBColor(0xF6, 0xF4, 0xEE)
PAPER = RGBColor(0xFF, 0xFD, 0xF8)
GREEN = RGBColor(0x1F, 0x6F, 0x5C)
DARKGREEN = RGBColor(0x12, 0x3F, 0x34)
DEEP = RGBColor(0x18, 0x2A, 0x22)
INK = RGBColor(0x1C, 0x2A, 0x22)
SOFT = RGBColor(0x45, 0x56, 0x4B)
MUTED = RGBColor(0x6D, 0x7B, 0x71)
LINE = RGBColor(0xDD, 0xD9, 0xCD)
TERRA = RGBColor(0xC9, 0x6F, 0x3B)
PEACH = RGBColor(0xF6, 0xE5, 0xD8)
LIGHTGREEN = RGBColor(0xE5, 0xF0, 0xEA)
PALEGREEN = RGBColor(0xEE, 0xF6, 0xF1)
BLUE = RGBColor(0x3B, 0x6E, 0xA8)
PALEBLUE = RGBColor(0xE7, 0xEE, 0xF7)
GOLD = RGBColor(0xB5, 0x86, 0x3A)
CODEBG = RGBColor(0x15, 0x25, 0x1F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT_BODY = "Microsoft YaHei"
FONT_SERIF = "SimSun"
FONT_MONO = "Consolas"

SW = Inches(13.333)
SH = Inches(7.5)

prs = Presentation()
prs.slide_width = SW
prs.slide_height = SH
BLANK = prs.slide_layouts[6]

SECTION_NAMES = {
    2: "01 · 选题",
    3: "02 · 用户",
    4: "03 · 需求",
    5: "04 · 架构",
    6: "05 · 数据库",
    7: "06 · 设计",
    8: "07 · 演示",
    9: "08 · 编辑器",
    10: "09 · 互动",
    11: "10 · 数据",
    12: "11 · 工程",
    13: "12 · 质量",
    14: "13 · 协作",
    15: "14 · 复盘",
    16: "15 · 总结",
}


# ---------- 基础绘图 ----------
def rgb(hex_value: str) -> RGBColor:
    value = hex_value.lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def add_bg(slide, color=CREAM):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def rect(slide, x, y, w, h, fill, line=None, radius=0.04, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    shp.shadow.inherit = False
    return shp


def line(slide, x1, y1, x2, y2, color=LINE, width=1.2, dash=None):
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(width)
    if dash:
        connector.line.dash_style = dash
    return connector


def set_font(run, font, size, color, bold=False, italic=False):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    # 同时设置东亚字体，避免中文回退到默认字体
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        element = rpr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}" + tag.split(":")[1])
        if element is None:
            from pptx.oxml.ns import qn
            from lxml import etree

            element = etree.SubElement(rpr, qn(tag))
        element.set("typeface", font)


def textbox(slide, text, x, y, w, h, size=18, color=INK, font=FONT_BODY,
            bold=False, italic=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
            line_spacing=1.15, margins=(0, 0, 0, 0)):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [Inches(v) for v in margins]
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    run = p.add_run()
    run.text = text
    set_font(run, font, size, color, bold, italic)
    return box


def rich_box(slide, runs, x, y, w, h, size=18, color=INK, font=FONT_BODY,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.15):
    """runs: list of dict(text, color, bold, font, size)。"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    for item in runs:
        run = p.add_run()
        run.text = item["text"]
        set_font(
            run,
            item.get("font", font),
            item.get("size", size),
            item.get("color", color),
            item.get("bold", False),
            item.get("italic", False),
        )
    return box


def eyebrow(slide, text, x=0.82, y=0.42, color=GREEN):
    textbox(slide, text, x, y, 9.6, 0.28, size=9, color=color, font=FONT_MONO, bold=True)


def title(slide, text, x=0.8, y=0.74, w=11.7, size=30, color=INK, font=FONT_SERIF):
    textbox(slide, text, x, y, w, 0.75, size=size, color=color, font=font, bold=True, line_spacing=1.03)


def subtitle(slide, text, x=0.82, y=1.5, w=11.3, size=13, color=MUTED):
    textbox(slide, text, x, y, w, 0.4, size=size, color=color)


def footer(slide, number, section=None):
    line(slide, 0.82, 7.03, 12.52, 7.03, LINE, 0.8)
    textbox(slide, "我的知识小栈 · 课程综合训练项目", 0.82, 7.12, 5.6, 0.2, 8, MUTED, FONT_MONO)
    if section:
        textbox(slide, section, 5.6, 7.12, 4.0, 0.2, 8, MUTED, FONT_MONO, align=PP_ALIGN.CENTER)
    textbox(slide, f"{number:02d} / 16", 11.5, 7.1, 1.0, 0.24, 9, GREEN, FONT_MONO, bold=True, align=PP_ALIGN.RIGHT)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def new_slide(bg=CREAM, number=None, section=None):
    slide = prs.slides.add_slide(BLANK)
    add_bg(slide, bg)
    if number:
        footer(slide, number, section)
    return slide


def pill(slide, text, x, y, w, fill=LIGHTGREEN, color=GREEN, size=9, mono=True):
    rect(slide, x, y, w, 0.32, fill, radius=0.5)
    textbox(slide, text, x + 0.12, y + 0.055, w - 0.24, 0.22, size, color,
            FONT_MONO if mono else FONT_BODY, bold=True, align=PP_ALIGN.CENTER)


def dot(slide, x, y, d, color):
    rect(slide, x, y, d, d, color, shape=MSO_SHAPE.OVAL, radius=0.5)


def bullet(slide, text, x, y, w, color=SOFT, size=11, marker_color=TERRA, gap=0.22):
    dot(slide, x, y + 0.075, 0.07, marker_color)
    textbox(slide, text, x + gap, y, w - gap, 0.35, size, color, line_spacing=1.2)


def image_cover(path: Path, width_in: float, height_in: float, name: str) -> Path:
    """按目标比例裁切图片，避免 PPT 拉伸变形。"""
    target_ratio = width_in / height_in
    image = Image.open(path).convert("RGB")
    w, h = image.size
    current = w / h
    if current > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        image = image.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = 0
        image = image.crop((0, top, w, top + new_h))
    image = ImageOps.fit(image, (1800, int(1800 / target_ratio)), method=Image.LANCZOS)
    out = ASSETS / name
    image.save(out, quality=92)
    return out


def add_picture(slide, path: Path, x, y, w, h, border=True):
    if border:
        rect(slide, x - 0.05, y - 0.05, w + 0.1, h + 0.1, PAPER, LINE, radius=0.03)
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))


def code_block(slide, text, x, y, w, h, size=8, dark=True):
    rect(slide, x, y, w, h, CODEBG if dark else PALEGREEN, CODEBG if dark else LINE, radius=0.04)
    box = slide.shapes.add_textbox(Inches(x + 0.14), Inches(y + 0.12), Inches(w - 0.28), Inches(h - 0.24))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.line_spacing = 1.35
    run = p.add_run()
    run.text = text
    set_font(run, FONT_MONO, size, RGBColor(0xDC, 0xEB, 0xE3) if dark else GREEN)


# ---------- 预裁切截图 ----------
home_crop = image_cover(ROOT / "deliverables/screenshot-home.png", 7.25, 4.75, "home-hero.jpg")
home_cover = image_cover(ROOT / "deliverables/screenshot-home.png", 5.21, 3.71, "home-cover.jpg")
post_crop = image_cover(ROOT / "deliverables/screenshot-post.png", 7.25, 5.18, "post-detail.jpg")
admin_crop = image_cover(ROOT / "deliverables/screenshot-admin.png", 7.35, 4.78, "admin-dashboard.jpg")


# =====================================================================
# 1 封面
# =====================================================================
s = new_slide(DARKGREEN)
# 装饰圆与线
rect(s, 8.9, -1.6, 5.6, 5.6, RGBColor(0x1B, 0x55, 0x46), shape=MSO_SHAPE.OVAL)
rect(s, 10.4, 1.0, 3.1, 3.1, DARKGREEN, rgb("#2A7560"), shape=MSO_SHAPE.OVAL)
line(s, 0.9, 1.05, 6.0, 1.05, TERRA, 1.4)
textbox(s, "COURSE PROJECT · 2026", 0.92, 1.18, 5.8, 0.3, 10, RGBColor(0xC7, 0xDA, 0xCF), FONT_MONO, True)
textbox(s, "我的知识小栈", 0.86, 1.72, 6.2, 1.0, 46, PAPER, FONT_SERIF, True)
textbox(s, "个人博客 / 笔记管理系统", 0.9, 2.78, 6.0, 0.55, 24, RGBColor(0xE9, 0xEF, 0xE9), FONT_BODY, False)
line(s, 0.92, 3.55, 3.3, 3.55, TERRA, 2)
textbox(s, "把零散的知识，收进一座会生长的小栈。", 0.9, 3.78, 6.0, 0.5, 15, RGBColor(0xB9, 0xCD, 0xC2), FONT_SERIF, False, True)
textbox(s, "Flask 3  ·  MySQL 8.0  ·  Vanilla HTML / CSS / JS", 0.92, 4.55, 6.2, 0.3, 10, RGBColor(0x8F, 0xB0, 0x9F), FONT_MONO)
textbox(s, "第 X 组  ·  课程综合训练项目  ·  2026", 0.92, 6.45, 6.1, 0.35, 11, RGBColor(0xD9, 0xE4, 0xDC), FONT_BODY)
textbox(s, "16 页  ·  8 分钟  ·  可运行系统", 0.92, 6.82, 5.0, 0.28, 9, RGBColor(0x7F, 0x9B, 0x8B), FONT_MONO)

# 截图卡片
card_x, card_y, card_w, card_h = 7.15, 1.55, 5.45, 3.95
rect(s, card_x, card_y, card_w, card_h, PAPER, None, radius=0.04)
s.shapes.add_picture(str(home_cover), Inches(card_x + 0.12), Inches(card_y + 0.12), Inches(card_w - 0.24), Inches(card_h - 0.24))
textbox(s, "HOME  /  LIGHT THEME", card_x + 0.18, card_y + card_h + 0.16, 3.5, 0.24, 8, RGBColor(0xA9, 0xC1, 0xB4), FONT_MONO, True)
textbox(s, "01", 11.75, 6.2, 0.8, 0.5, 24, TERRA, FONT_MONO, True, align=PP_ALIGN.RIGHT)
add_notes(s, "大家好，我们是第 X 组。我们的项目叫「我的知识小栈」——一个把零散学习笔记收进一座会生长的个人博客系统。下面用 8 分钟介绍我们做了什么，以及为什么这样做。")

# =====================================================================
# 2 背景
# =====================================================================
s = new_slide(number=2, section=SECTION_NAMES[2])
eyebrow(s, "01  /  WHY THIS STACK")
title(s, "为什么需要一座「知识小栈」？")
subtitle(s, "学习内容越来越多，真正能复用的经验却越来越少。")
line(s, 0.82, 1.95, 6.05, 1.95, LINE, 1)
textbox(s, "不是工具不够多，\n而是缺少一个\n属于自己的知识入口。", 0.82, 2.25, 5.2, 1.75, 27, GREEN, FONT_SERIF, True, line_spacing=1.2)
textbox(s, "我们把痛点拆成三件事：找不到、留不住、讲不清。", 0.86, 4.35, 5.4, 0.5, 12, SOFT, line_spacing=1.4)

items = [
    ("01", "找不到", "教程、报错、项目笔记散落在收藏夹、聊天记录和本地文档里。"),
    ("02", "留不住", "只收藏不加工，资料越存越多，真正能调用的经验很少。"),
    ("03", "讲不清", "项目做完没有结构化复盘，答辩、简历和面试都说不清楚。"),
]
for i, (num, head, body) in enumerate(items):
    y = 1.7 + i * 1.5
    rect(s, 7.45, y, 5.05, 1.28, PAPER, LINE, radius=0.05)
    textbox(s, num, 7.7, y + 0.18, 0.6, 0.3, 10, TERRA, FONT_MONO, True)
    textbox(s, head, 8.28, y + 0.15, 1.25, 0.35, 17, INK, FONT_SERIF, True)
    textbox(s, body, 8.28, y + 0.6, 3.9, 0.5, 10.5, SOFT, line_spacing=1.35)

rect(s, 0.82, 6.18, 11.7, 0.55, LIGHTGREEN, None, radius=0.4)
rich_box(s, [
    {"text": "需要的不是“记事本”", "color": GREEN, "bold": True, "size": 11},
    {"text": "  ·  而是一条 收集 → 加工 → 输出 的闭环", "color": SOFT, "size": 11},
], 1.05, 6.3, 11.1, 0.28)
add_notes(s, "我们都有过这样的经历：明明之前解决过某个报错，却怎么也找不到当时的记录；收藏了几百篇文章，真正用上的没几篇。问题不是工具不够多，而是缺少一个自己的知识入口。所以我们想做一个真正会用的个人博客 / 笔记系统，而不是为了交作业临时拼一个 CRUD。")

# =====================================================================
# 3 用户角色
# =====================================================================
s = new_slide(number=3, section=SECTION_NAMES[3])
eyebrow(s, "02  /  USERS & SCENARIOS")
title(s, "三种角色，一条完整的使用链路")
subtitle(s, "一个站主 + 多位访客；公开注册不授予后台权限。")

roles = [
    ("访", "访客", "Visitor", ["浏览首页与文章", "搜索 / 分类 / 标签", "提交游客评论"], PAPER, INK, GREEN),
    ("读", "注册读者", "Reader", ["收藏 / 取消收藏", "以账号身份评论", "查看评论审核状态"], GREEN, PAPER, PAPER),
    ("博", "博主", "Admin", ["文章 / 分类 / 标签", "评论审核与附件", "数据看板与设置"], PAPER, INK, TERRA),
]
role_tags = ["无需登录", "注册即用", "唯一管理者"]
for i, (mark, name, en, bullets, bg, fg, accent) in enumerate(roles):
    x = 0.82 + i * 4.12
    rect(s, x, 1.82, 3.82, 3.62, bg, LINE if bg == PAPER else None, radius=0.05)
    dot(s, x + 0.25, 2.05, 0.55, accent if bg == PAPER else PAPER)
    textbox(s, mark, x + 0.25, 2.18, 0.55, 0.25, 10, PAPER if bg == GREEN else accent, FONT_SERIF, True, align=PP_ALIGN.CENTER)
    textbox(s, name, x + 0.25, 2.78, 3.2, 0.4, 21, fg, FONT_SERIF, True)
    textbox(s, en.upper(), x + 0.27, 3.2, 3.0, 0.24, 8, fg if bg == GREEN else MUTED, FONT_MONO)
    for j, item in enumerate(bullets):
        line(s, x + 0.27, 3.62 + j * 0.47, x + 3.55, 3.62 + j * 0.47, fg if bg == GREEN else LINE, 0.7)
        textbox(s, item, x + 0.27, 3.72 + j * 0.47, 3.2, 0.28, 10.5, fg if bg == GREEN else SOFT)
    pill(s, role_tags[i], x + 0.27, 5.02, 1.0, rgb("#2A7560") if bg == GREEN else CREAM,
         PAPER if bg == GREEN else accent, 7)

# 时间线
line(s, 0.95, 6.1, 12.25, 6.1, LINE, 1.2)
steps = ["写笔记", "分类打标", "发布", "被阅读 / 搜索", "评论审核", "看板复盘"]
for i, step in enumerate(steps):
    x = 0.95 + i * 2.25
    dot(s, x - 0.055, 6.045, 0.11, GREEN if i < 5 else TERRA)
    textbox(s, step, x - 0.55, 6.26, 1.3, 0.28, 9, SOFT, FONT_BODY, align=PP_ALIGN.CENTER)
add_notes(s, "我们把角色收敛成三类。访客不需要注册就能读和留言；注册读者可以收藏、用账号评论；博主是唯一的内容管理者。这样既保留了注册流程，又符合个人博客“一个站主 + 多位访客”的真实语义，避免任何人注册就能进后台。")

# =====================================================================
# 4 需求范围
# =====================================================================
s = new_slide(number=4, section=SECTION_NAMES[4])
eyebrow(s, "03  /  SCOPE")
title(s, "需求范围：5 项主体 + 6 项扩展")
subtitle(s, "先闭环，再加分；每个扩展都能在现场走通。")

rect(s, 0.82, 1.78, 5.35, 4.72, PAPER, LINE, radius=0.05)
textbox(s, "5", 1.08, 1.95, 1.1, 0.82, 48, GREEN, FONT_SERIF, True)
textbox(s, "主体基础功能", 2.02, 2.12, 3.6, 0.38, 18, INK, FONT_SERIF, True)
textbox(s, "课程任务书要求，全部打通", 2.03, 2.5, 3.2, 0.26, 9, MUTED)
main_items = [
    ("01", "登录注册", "博主登录 · 读者注册"),
    ("02", "文章 CRUD", "发布 / 编辑 / 草稿 / 删除"),
    ("03", "分类与标签", "增删改查 · 多选标签"),
    ("04", "浏览与分页", "首页 / 列表 / 详情"),
    ("05", "文章搜索", "标题 / 摘要 / 正文"),
]
for i, (num, head, desc) in enumerate(main_items):
    y = 2.88 + i * 0.68
    textbox(s, num, 1.08, y, 0.42, 0.26, 8, TERRA, FONT_MONO, True)
    textbox(s, head, 1.6, y - 0.02, 1.9, 0.3, 11, INK, FONT_BODY, True)
    textbox(s, desc, 3.65, y, 2.3, 0.26, 8.5, MUTED)

ext = [
    ("E1", "Markdown 编辑器", "实时预览 · 工具栏"),
    ("E2", "文章收藏", "联合主键 · 我的收藏"),
    ("E3", "评论审核", "先审后发 · 状态机"),
    ("E4", "双主题", "CSS 变量 · 记忆"),
    ("E5", "图片附件", "真实校验 · 附件库"),
    ("E6", "数据看板", "7 日趋势 · 分类分布"),
]
for i, (num, head, desc) in enumerate(ext):
    col, row = i % 2, i // 2
    x = 6.62 + col * 3.02
    y = 1.78 + row * 1.57
    rect(s, x, y, 2.86, 1.38, PAPER, LINE, radius=0.05)
    pill(s, num, x + 0.17, y + 0.15, 0.48, PEACH, TERRA, 8)
    textbox(s, head, x + 0.17, y + 0.55, 2.45, 0.3, 12, INK, FONT_BODY, True)
    textbox(s, desc, x + 0.17, y + 0.92, 2.45, 0.25, 8.3, MUTED)

textbox(s, "主体 100% 可演示  ·  扩展 6 项全部可演示  ·  不为凑数做“假入口”", 0.86, 6.62, 11.6, 0.28, 9, GREEN, FONT_MONO, True)
add_notes(s, "需求上我们没有贪多。主体五项全部打通，扩展做了六项，并且每一项都不是“摆设”：Markdown 有实时预览和安全过滤，评论有审核状态机，看板有真实浏览明细。先保证闭环，再逐步加分。")

# =====================================================================
# 5 技术架构
# =====================================================================
s = new_slide(number=5, section=SECTION_NAMES[5])
eyebrow(s, "04  /  ARCHITECTURE")
title(s, "技术选型：够用、能讲、好部署")
subtitle(s, "单体 Web 应用 + 应用工厂 + 蓝图模块化。")

stack = [
    ("Flask 3", "Web 框架"),
    ("MySQL 8.0", "关系数据库"),
    ("SQLAlchemy", "ORM / 事务"),
    ("Jinja2", "服务端模板"),
    ("Vanilla JS", "渐进增强"),
    ("Docker", "一键部署"),
]
for i, (head, desc) in enumerate(stack):
    col, row = i % 2, i // 2
    x = 0.82 + col * 2.55
    y = 1.8 + row * 1.34
    rect(s, x, y, 2.32, 1.12, PAPER, LINE, radius=0.05)
    textbox(s, head, x + 0.17, y + 0.19, 2.0, 0.32, 13, GREEN, FONT_MONO, True)
    textbox(s, desc, x + 0.17, y + 0.63, 2.0, 0.25, 9, MUTED)

# 架构图
bx, by, bw = 6.6, 1.58, 5.95
rect(s, bx, by, bw, 0.55, PAPER, LINE, radius=0.04)
textbox(s, "浏览器  ·  桌面 / 手机", bx, by + 0.15, bw, 0.24, 10, SOFT, FONT_BODY, align=PP_ALIGN.CENTER)
line(s, bx + bw / 2, by + 0.56, bx + bw / 2, by + 0.78, GREEN, 1.4)
rect(s, bx, by + 0.8, bw, 1.2, DARKGREEN, None, radius=0.04)
textbox(s, "Flask 应用  /  Gunicorn", bx + 0.2, by + 0.94, 3.0, 0.28, 11, PAPER, FONT_BODY, True)
mods = ["main", "auth", "account", "admin", "api"]
for i, mod in enumerate(mods):
    pill(s, mod, bx + 0.2 + i * 1.08, by + 1.42, 0.92, rgb("#2A7560"), PAPER, 7)
line(s, bx + bw / 2, by + 2.02, bx + bw / 2, by + 2.22, GREEN, 1.4)
rect(s, bx, by + 2.24, bw, 0.5, LIGHTGREEN, None, radius=0.04)
textbox(s, "SQLAlchemy ORM  ·  预加载 / 事务 / 参数化", bx, by + 2.38, bw, 0.22, 9.5, GREEN, FONT_MONO, align=PP_ALIGN.CENTER)
line(s, bx + 1.5, by + 2.75, bx + 1.5, by + 3.0, GREEN, 1.4)
line(s, bx + 4.45, by + 2.75, bx + 4.45, by + 3.0, GREEN, 1.4)
rect(s, bx, by + 3.02, 2.9, 0.72, PAPER, LINE, radius=0.04)
textbox(s, "MySQL 8.0\n9 张表 · InnoDB · utf8mb4", bx + 0.16, by + 3.12, 2.55, 0.5, 8.5, SOFT)
rect(s, bx + 3.05, by + 3.02, 2.9, 0.72, PAPER, LINE, radius=0.04)
textbox(s, "static/uploads\n图片附件 · 命名卷持久化", bx + 3.21, by + 3.12, 2.55, 0.5, 8.5, SOFT)

textbox(s, "为什么不是微服务 / 前后端分离？", 0.84, 5.92, 3.7, 0.28, 10, INK, FONT_BODY, True)
textbox(s, "当前规模不需要额外运维成本；单体 + 服务端渲染让权限、SEO、部署都更简单。", 0.84, 6.26, 11.5, 0.42, 10, MUTED, line_spacing=1.35)
add_notes(s, "技术栈刻意保持简单。后端 Flask，数据库 MySQL 8.0，前端是服务端渲染加原生 JS。没有 Vue/React，也没有 Redis 和微服务。不是不会，而是当前项目不需要——我们希望每一行代码都能在答辩时讲清楚为什么存在。")

# =====================================================================
# 6 数据库
# =====================================================================
s = new_slide(number=6, section=SECTION_NAMES[6])
eyebrow(s, "05  /  DATABASE")
title(s, "数据库：9 张表，把关系讲清楚")
subtitle(s, "InnoDB · utf8mb4 · 外键 + 组合索引 + CHECK", w=4.5, size=11)

# 表卡片
tables = {
    "users": (0.75, 1.85, 1.45, 0.62, GREEN, PAPER),
    "posts": (2.85, 1.85, 1.7, 0.62, DARKGREEN, PAPER),
    "categories": (0.75, 3.15, 1.45, 0.55, PAPER, INK),
    "tags": (2.85, 3.15, 1.3, 0.55, PAPER, INK),
    "post_tags": (2.85, 4.08, 1.3, 0.5, PEACH, TERRA),
    "comments": (5.45, 1.55, 1.55, 0.55, PAPER, INK),
    "favorites": (5.45, 2.48, 1.55, 0.55, PAPER, INK),
    "post_views": (5.45, 3.41, 1.55, 0.55, PAPER, INK),
    "attachments": (0.75, 4.88, 1.55, 0.55, PAPER, INK),
}
for name, (x, y, w, h, fill, fg) in tables.items():
    rect(s, x, y, w, h, fill, None if fill != PAPER else LINE, radius=0.06)
    textbox(s, name, x, y + 0.15, w, 0.28, 10, fg, FONT_MONO, True, align=PP_ALIGN.CENTER)

# 连线
line(s, 2.2, 2.16, 2.85, 2.16, LINE, 1.2)
line(s, 2.2, 2.16, 2.2, 3.15, LINE, 1.0)
line(s, 2.2, 3.42, 2.85, 3.42, LINE, 1.0)
line(s, 4.55, 2.16, 5.45, 1.83, LINE, 1.0)
line(s, 4.55, 2.16, 5.45, 2.75, LINE, 1.0)
line(s, 4.55, 2.16, 5.45, 3.68, LINE, 1.0)
line(s, 3.45, 2.47, 3.45, 4.08, LINE, 1.0)
line(s, 1.48, 2.47, 1.48, 4.88, LINE, 1.0)
textbox(s, "1 : N", 2.28, 1.93, 0.55, 0.2, 7, TERRA, FONT_MONO, True)
textbox(s, "M : N", 3.04, 3.66, 0.55, 0.2, 7, TERRA, FONT_MONO, True)

# 右侧设计取舍
textbox(s, "设计取舍", 7.55, 1.72, 3.0, 0.35, 16, INK, FONT_SERIF, True)
choices = [
    ("01", "utf8mb4", "中文与 emoji 一次解决；连接串也强制 charset。"),
    ("02", "Markdown + HTML", "编辑用原文，展示用已过滤 HTML，读取不重复渲染。"),
    ("03", "联合主键", "favorites(user_id, post_id) 从数据库层防止重复收藏。"),
    ("04", "汇总 + 明细", "view_count 排序；post_views 支撑 7 日趋势。"),
    ("05", "状态机", "评论 pending → approved / rejected，可回退、可审计。"),
]
for i, (num, head, desc) in enumerate(choices):
    y = 2.2 + i * 0.83
    textbox(s, num, 7.58, y, 0.35, 0.2, 7.5, TERRA, FONT_MONO, True)
    textbox(s, head, 8.0, y - 0.04, 1.85, 0.26, 10, GREEN, FONT_MONO, True)
    textbox(s, desc, 8.0, y + 0.24, 4.25, 0.4, 8.2, MUTED, line_spacing=1.3)

pill(s, "9 TABLES", 0.78, 6.28, 1.15, LIGHTGREEN, GREEN, 8)
pill(s, "20+ INDEXES", 2.05, 6.28, 1.48, PEACH, TERRA, 8)
pill(s, "FOREIGN KEYS", 3.45, 6.28, 1.55, PAPER, INK, 8)
textbox(s, "分类删除 SET NULL，文章不丢；文章删除 CASCADE，评论 / 收藏 / 浏览一起清理。", 0.8, 6.66, 11.8, 0.28, 8.5, MUTED, line_spacing=1.2)
add_notes(s, "数据库一共 9 张表。核心是 users、posts、categories、tags，以及评论、收藏、附件、浏览明细和文章标签关联表。这里有两个我们比较满意的取舍：第一，文章同时存 Markdown 原文和过滤后的 HTML，编辑用原文、展示用 HTML；第二，浏览量既有汇总字段方便排序，又有明细表支撑 7 日趋势。")

# =====================================================================
# 7 视觉
# =====================================================================
s = new_slide(number=7, section=SECTION_NAMES[7])
eyebrow(s, "06  /  VISUAL DESIGN")
title(s, "界面不是模板：一套变量，覆盖 20+ 页面")
subtitle(s, "纸张感 · 深绿 + 陶土 · 衬线标题 · 统一设计令牌。")

features = [
    ("纸张感", "米白背景、细网格、层叠便签；封面全部本地 SVG，断网也能看。", PEACH, TERRA),
    ("统一", "按钮、卡片、表单、标签共享一套 token；后台与前台同一套语言。", LIGHTGREEN, GREEN),
    ("双主题", "data-theme + CSS 变量 + localStorage；不是复制第二套样式。", PALEBLUE, BLUE),
]
for i, (head, desc, bg, fg) in enumerate(features):
    y = 1.85 + i * 1.5
    rect(s, 0.82, y, 4.05, 1.28, bg, None, radius=0.05)
    textbox(s, head, 1.02, y + 0.18, 3.55, 0.3, 14, fg, FONT_SERIF, True)
    textbox(s, desc, 1.02, y + 0.58, 3.6, 0.52, 8.8, SOFT, line_spacing=1.35)

add_picture(s, home_crop, 5.15, 1.63, 7.4, 4.85)
textbox(s, "首页 · 浅色主题 · 1440px", 5.2, 6.58, 4.2, 0.25, 8, MUTED, FONT_MONO)
textbox(s, "没有 UI 框架，也没有 CDN 依赖。", 9.55, 6.55, 3.1, 0.25, 8, GREEN, FONT_MONO, True, align=PP_ALIGN.RIGHT)
add_notes(s, "视觉上我们不想做成通用后台模板。用了米白纸感、深绿主色和陶土色点缀，标题用衬线字体，希望像一个有人认真整理的地方。所有页面共享一套 CSS 变量，所以暗黑模式不是复制一套样式，而是换一组变量。手机端也做了完整适配。")

# =====================================================================
# 8 主体闭环
# =====================================================================
s = new_slide(number=8, section=SECTION_NAMES[8])
eyebrow(s, "07  /  CORE FLOW")
title(s, "主体闭环：从搜索到发布，一条动线走完")
subtitle(s, "现场演示 45 秒：搜索 → 详情 → 发文 → 前台验证。")

steps = [
    ("01", "搜索与筛选", "关键词 Flask；再叠加分类 / 标签。"),
    ("02", "读一篇详情", "正文、目录、收藏、评论。"),
    ("03", "登录博主发文", "标题 / 分类 / 标签 / Markdown。"),
    ("04", "发布并验证", "前台出现；草稿仅博主可见。"),
]
for i, (num, head, desc) in enumerate(steps):
    y = 1.78 + i * 1.16
    dot(s, 0.92, y + 0.03, 0.48, GREEN if i < 3 else TERRA)
    textbox(s, num, 0.92, y + 0.1, 0.48, 0.22, 8, PAPER, FONT_MONO, True, align=PP_ALIGN.CENTER)
    textbox(s, head, 1.62, y - 0.02, 3.3, 0.3, 13, INK, FONT_BODY, True)
    textbox(s, desc, 1.62, y + 0.31, 3.5, 0.4, 9, MUTED, line_spacing=1.3)

add_picture(s, post_crop, 5.35, 1.52, 7.25, 5.18)
textbox(s, "文章详情 · Markdown / 自动目录 / 评论", 5.4, 6.78, 6.6, 0.2, 8, MUTED, FONT_MONO)
add_notes(s, "主体功能我们用一条动线演示：先在首页搜索 Flask，看到分类和标签筛选；然后登录博主，在后台写一篇新文章，选分类、打标签、发布；回到前台，文章出现在列表和详情；最后演示编辑、转草稿和删除。整个过程不需要重启服务，数据实时生效。")

# =====================================================================
# 9 Markdown 编辑器（界面 mock）
# =====================================================================
s = new_slide(number=9, section=SECTION_NAMES[9])
eyebrow(s, "08  /  MARKDOWN EDITOR")
title(s, "Markdown 编辑器：写得顺，也守得住")
subtitle(s, "左写右看 · 服务端统一渲染 · 安全过滤", w=3.55, size=10.5)

points = [
    ("实时预览", "后端统一渲染，预览与详情一致。"),
    ("安全过滤", "唯一 |safe 入口，白名单标签 / 属性 / 协议。"),
    ("图片即插", "按钮、粘贴、拖拽；上传后自动插入 Markdown。"),
]
for i, (head, desc) in enumerate(points):
    y = 1.82 + i * 1.35
    textbox(s, f"0{i + 1}", 0.86, y, 0.36, 0.22, 8, TERRA, FONT_MONO, True)
    textbox(s, head, 0.86, y + 0.23, 3.35, 0.3, 13, INK, FONT_SERIF, True)
    textbox(s, desc, 0.86, y + 0.62, 3.5, 0.45, 8.8, MUTED, line_spacing=1.35)

# 编辑器外框
ex, ey, ew, eh = 4.65, 1.52, 7.95, 5.55
rect(s, ex, ey, ew, eh, PAPER, LINE, radius=0.03)
textbox(s, "课堂演示：如何用 3 步整理一条笔记", ex + 0.22, ey + 0.16, 6.7, 0.32, 13, INK, FONT_SERIF, True)
textbox(s, "0 / 150", ex + ew - 0.85, ey + 0.22, 0.65, 0.2, 6.5, MUTED, FONT_MONO, align=PP_ALIGN.RIGHT)

# 工具栏
rect(s, ex + 0.12, ey + 0.62, ew - 0.24, 0.34, CREAM, None, radius=0.02)
tools = ["B", "I", "H2", "H3", "</>", "•", ">", "▦", "IMG", "预览"]
for i, tool in enumerate(tools[:9]):
    x = ex + 0.24 + i * 0.36
    rect(s, x, ey + 0.68, 0.28, 0.22, PAPER, LINE, radius=0.12)
    textbox(s, tool, x, ey + 0.705, 0.28, 0.16, 6, SOFT, FONT_MONO, align=PP_ALIGN.CENTER)
pill(s, "PREVIEW", ex + ew - 1.15, ey + 0.67, 0.9, LIGHTGREEN, GREEN, 6)

# 左右分栏
split = ex + ew * 0.52
line(s, split, ey + 1.0, split, ey + eh - 0.35, LINE, 1)
code_text = (
    "## 为什么要整理笔记？\n\n"
    "因为 **能复用的知识** 才有价值。\n\n"
    "### 三个步骤\n\n"
    "1. 记录场景\n"
    "2. 写下结论\n"
    "3. 补充反例\n\n"
    "> 一条好笔记，应该能回答\n"
    "> 一个真实问题。\n\n"
    "```python\n"
    "def organize(note):\n"
    "    return note.strip()\n"
    "```"
)
code_box = s.shapes.add_textbox(Inches(ex + 0.2), Inches(ey + 1.12), Inches(split - ex - 0.35), Inches(4.1))
tf = code_box.text_frame
tf.word_wrap = True
tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
for idx, line_text in enumerate(code_text.split("\n")):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.line_spacing = 1.25
    r = p.add_run()
    r.text = line_text or " "
    set_font(r, FONT_MONO, 6.8, RGBColor(0x3E, 0x50, 0x45))

# 预览区
rect(s, split + 0.1, ey + 1.06, ew - (split - ex) - 0.25, eh - 1.5, rgb("#FAF8F1"), None, radius=0.02)
textbox(s, "实时预览", split + 0.26, ey + 1.16, 1.2, 0.2, 6, MUTED, FONT_MONO, True)
textbox(s, "为什么要整理笔记？", split + 0.26, ey + 1.48, 3.3, 0.3, 13, INK, FONT_SERIF, True)
rich_box(s, [
    {"text": "因为 ", "color": SOFT, "size": 7.5},
    {"text": "能复用的知识", "color": INK, "bold": True, "size": 7.5},
    {"text": " 才有价值。", "color": SOFT, "size": 7.5},
], split + 0.26, ey + 1.88, 3.2, 0.25)
textbox(s, "三个步骤", split + 0.26, ey + 2.23, 2.0, 0.24, 9.5, INK, FONT_SERIF, True)
for i, item in enumerate(["记录场景", "写下结论", "补充反例"]):
    textbox(s, f"{i + 1}.  {item}", split + 0.28, ey + 2.55 + i * 0.26, 2.2, 0.2, 7, SOFT)
rect(s, split + 0.26, ey + 3.43, 3.25, 0.6, PEACH, None, radius=0.03)
textbox(s, "一条好笔记，应该能回答一个真实问题。", split + 0.38, ey + 3.54, 3.0, 0.38, 7, TERRA, FONT_SERIF, italic=True)
textbox(s, "图片上传成功，已插入正文", split + 0.26, ey + 4.7, 3.2, 0.2, 6.2, GREEN, FONT_MONO, True)
add_notes(s, "编辑器不是简单放一个 textarea。左侧写 Markdown，右侧实时预览，带工具栏和快捷键。预览不是前端随便渲染，而是走后端统一渲染并做 bleach 白名单过滤，保证预览和最终详情一致，也避免存储型 XSS。图片可以点按钮、粘贴或拖拽上传，自动插入 Markdown。")

# =====================================================================
# 10 评论审核与收藏
# =====================================================================
s = new_slide(number=10, section=SECTION_NAMES[10])
eyebrow(s, "09  /  INTERACTION")
title(s, "评论先审后发，收藏不重复")
subtitle(s, "开放讨论，但不把垃圾评论直接放到读者面前。")

textbox(s, "评论状态机", 0.86, 1.75, 2.2, 0.3, 13, INK, FONT_SERIF, True)
# 状态卡
rect(s, 1.0, 2.55, 1.55, 0.62, PEACH, None, radius=0.3)
textbox(s, "PENDING", 1.0, 2.69, 1.55, 0.24, 8, TERRA, FONT_MONO, True, align=PP_ALIGN.CENTER)
rect(s, 3.95, 1.95, 1.55, 0.62, LIGHTGREEN, None, radius=0.3)
textbox(s, "APPROVED", 3.95, 2.09, 1.55, 0.24, 8, GREEN, FONT_MONO, True, align=PP_ALIGN.CENTER)
rect(s, 3.95, 3.15, 1.55, 0.62, rgb("#F8E6E4"), None, radius=0.3)
textbox(s, "REJECTED", 3.95, 3.29, 1.55, 0.24, 8, RGBColor(0xAD, 0x3F, 0x3F), FONT_MONO, True, align=PP_ALIGN.CENTER)
line(s, 2.55, 2.85, 3.95, 2.26, GREEN, 1.2)
line(s, 2.55, 2.85, 3.95, 3.46, RGBColor(0xAD, 0x3F, 0x3F), 1.2)
textbox(s, "通过", 2.95, 2.35, 0.6, 0.2, 7, GREEN, FONT_MONO, True)
textbox(s, "驳回", 2.95, 3.2, 0.6, 0.2, 7, RGBColor(0xAD, 0x3F, 0x3F), FONT_MONO, True)
textbox(s, "未审核不公开；审核记录时间与审核人；支持重新通过。", 1.0, 4.05, 5.3, 0.35, 8.5, MUTED)

# 防护措施
security = [("蜜罐字段", 0.86), ("20 秒限频", 2.0), ("纯文本输出", 3.27), ("2–800 字", 4.55)]
for label, x in security:
    pill(s, label, x, 4.75, 1.05 if len(label) < 7 else 1.25, PAPER, GREEN, 7)

# 收藏卡
rect(s, 7.3, 1.7, 5.15, 3.9, PAPER, LINE, radius=0.05)
textbox(s, "收藏", 7.58, 1.94, 1.0, 0.32, 17, INK, FONT_SERIF, True)
textbox(s, "SAVED NOTES", 8.6, 2.03, 1.4, 0.2, 7, MUTED, FONT_MONO)
# 迷你文章卡
rect(s, 7.58, 2.45, 4.6, 0.78, CREAM, None, radius=0.03)
rect(s, 7.7, 2.55, 0.55, 0.55, GREEN, None, radius=0.05)
textbox(s, "从零搭建一座会生长的知识栈", 8.4, 2.56, 3.55, 0.26, 9, INK, FONT_BODY, True)
textbox(s, "学习方法 · 2 分钟阅读", 8.4, 2.86, 3.2, 0.2, 7, MUTED)
rect(s, 7.58, 3.4, 1.55, 0.42, PEACH, None, radius=0.3)
textbox(s, "★ 已收藏 12", 7.58, 3.49, 1.55, 0.22, 7.5, TERRA, FONT_BODY, True, align=PP_ALIGN.CENTER)
textbox(s, "联合主键 (user_id, post_id)", 9.35, 3.44, 2.9, 0.22, 7.5, MUTED, FONT_MONO)
line(s, 7.58, 4.08, 12.2, 4.08, LINE, 0.8)
textbox(s, "读者在账号中心查看收藏；未登录点击收藏会先引导登录。", 7.58, 4.28, 4.5, 0.42, 8, MUTED, line_spacing=1.3)
textbox(s, "“开放讨论，但不把垃圾评论直接放到读者面前。”", 7.55, 5.95, 4.9, 0.55, 12, GREEN, FONT_SERIF, italic=True)
add_notes(s, "评论采用“先审后发”。访客和读者都能留言，但默认进入待审核，后台可以通过、驳回、删除。为了防止简单刷评论，加了蜜罐字段、20 秒限频和长度校验。收藏用联合主键防重复，读者在账号中心能看到自己的收藏列表。")

# =====================================================================
# 11 图片与看板
# =====================================================================
s = new_slide(number=11, section=SECTION_NAMES[11])
eyebrow(s, "10  /  MEDIA & DASHBOARD")
title(s, "让数据说话，也让图片安全落地")
subtitle(s, "浏览明细支撑趋势；图片上传真实解码。", w=4.3, size=11)

add_picture(s, admin_crop, 5.3, 1.55, 7.35, 4.78)
textbox(s, "后台看板 · 7 日趋势 / 分类分布 / 待审队列", 5.35, 6.45, 6.9, 0.22, 8, MUTED, FONT_MONO)

left_items = [
    ("7 日趋势", "post_views 明细按日期聚合，会话去重。"),
    ("分类分布", "categories LEFT JOIN posts，环形图纯 CSS。"),
    ("待审队列", "评论进入 pending，侧栏显示角标。"),
    ("图片安全", "Pillow 解码 + 格式白名单 + UUID 重命名。"),
]
for i, (head, desc) in enumerate(left_items):
    y = 1.75 + i * 1.08
    textbox(s, f"0{i + 1}", 0.86, y, 0.3, 0.2, 7.5, TERRA, FONT_MONO, True)
    textbox(s, head, 1.2, y - 0.03, 1.75, 0.26, 11, INK, FONT_BODY, True)
    textbox(s, desc, 1.2, y + 0.27, 3.6, 0.36, 8.2, MUTED, line_spacing=1.3)

pill(s, "5MB LIMIT", 0.86, 6.2, 1.15, PEACH, TERRA, 7)
pill(s, "UPLOAD / YYYY / MM", 2.12, 6.2, 2.0, LIGHTGREEN, GREEN, 7)
textbox(s, "不信任扩展名；SVG 不在白名单。", 0.86, 6.62, 4.0, 0.22, 8, MUTED)
add_notes(s, "图片上传不信任扩展名，用 Pillow 真正解码，只接受 JPEG/PNG/GIF/WEBP，UUID 重命名，防止脚本伪装和覆盖。看板展示文章、阅读、评论、收藏，以及近 7 天趋势和分类分布。图表是纯 CSS 实现的，不依赖 Chart.js，断网也能演示。")

# =====================================================================
# 12 工程细节
# =====================================================================
s = new_slide(number=12, section=SECTION_NAMES[12])
eyebrow(s, "11  /  ENGINEERING DETAILS")
title(s, "四个容易被忽略的工程细节")
subtitle(s, "“能跑”之后，再问一句：为什么这样写？")

cards = [
    ("01", "应用工厂", "可测试、可配置、避免全局状态", "def create_app(test_config=None):\n    app.config.from_object(Config)\n    if test_config:\n        app.config.update(test_config)"),
    ("02", "权限校验", "后台统一 before_request，不靠模板隐藏", "@admin_bp.before_request\ndef require_admin():\n    if not current_user.is_admin:\n        abort(403)"),
    ("03", "安全渲染", "Markdown 之后必须过 bleach 白名单", "cleaned = bleach.clean(\n    rendered, tags=ALLOWED_TAGS,\n    attributes=ALLOWED_ATTRIBUTES)"),
    ("04", "查询预加载", "多对一 joinedload，多对多 selectinload", "stmt.options(\n    joinedload(Post.category),\n    selectinload(Post.tags))"),
]
for i, (num, head, desc, code) in enumerate(cards):
    col, row = i % 2, i // 2
    x = 0.82 + col * 5.98
    y = 1.78 + row * 2.32
    rect(s, x, y, 5.62, 2.04, PAPER, LINE, radius=0.04)
    textbox(s, num, x + 0.2, y + 0.17, 0.35, 0.2, 7, TERRA, FONT_MONO, True)
    textbox(s, head, x + 0.62, y + 0.12, 2.2, 0.28, 12, INK, FONT_BODY, True)
    textbox(s, desc, x + 0.62, y + 0.44, 4.7, 0.22, 7.8, MUTED)
    code_block(s, code, x + 0.2, y + 0.78, 5.2, 1.08, 6.3)

textbox(s, "“代码不是写完就算，能解释、能测试、能回滚，才算完成。”", 0.86, 6.45, 11.4, 0.35, 11, GREEN, FONT_SERIF, italic=True, align=PP_ALIGN.CENTER)
add_notes(s, "这里挑四个点。第一，应用工厂让测试可以注入独立数据库；第二，后台权限统一在 before_request 校验，不依赖模板隐藏；第三，Markdown 渲染后必须过 bleach，正文是唯一使用 safe 的地方；第四，列表查询用 joinedload 和 selectinload 预加载，避免 N+1。这些是课程项目里最容易踩、也最值得讲的点。")

# =====================================================================
# 13 测试
# =====================================================================
s = new_slide(number=13, section=SECTION_NAMES[13])
eyebrow(s, "12  /  QUALITY")
title(s, "不靠“点一遍”：13 个自动化用例")
subtitle(s, "独立 SQLite · 不碰演示数据 · CI 每次 push 自动跑", w=5.5, size=11)

textbox(s, "13", 0.86, 1.82, 2.0, 1.2, 74, GREEN, FONT_SERIF, True)
textbox(s, "自动化用例", 0.92, 3.05, 2.0, 0.3, 13, INK, FONT_BODY, True)
textbox(s, "覆盖登录、权限、CRUD、搜索、\n评论审核、收藏、XSS、上传。", 0.92, 3.45, 3.2, 0.7, 8.5, MUTED, line_spacing=1.45)

coverage = ["页面渲染", "登录 / 权限", "文章 CRUD", "搜索", "评论审核", "收藏", "XSS 过滤", "图片上传", "后台冒烟", "越权重定向"]
for i, item in enumerate(coverage):
    col, row = i % 2, i // 2
    x = 0.92 + col * 1.65
    y = 4.38 + row * 0.42
    textbox(s, "✓", x, y, 0.2, 0.2, 8, GREEN, FONT_BODY, True)
    textbox(s, item, x + 0.22, y, 1.4, 0.2, 7.5, SOFT)

# 终端卡
rect(s, 6.55, 1.7, 5.95, 3.75, CODEBG, None, radius=0.04)
dot(s, 6.78, 1.92, 0.08, TERRA)
dot(s, 6.94, 1.92, 0.08, rgb("#D9B36C"))
dot(s, 7.1, 1.92, 0.08, GREEN)
textbox(s, "terminal", 7.3, 1.86, 1.2, 0.2, 7, rgb("#7F9B8B"), FONT_MONO)
textbox(s, "$ pytest -q", 6.82, 2.3, 4.8, 0.28, 12, rgb("#8FD3B8"), FONT_MONO, True)
textbox(s, ".............", 6.82, 2.78, 4.8, 0.28, 12, RGBColor(0xDC, 0xEB, 0xE3), FONT_MONO)
textbox(s, "[100%]", 11.15, 2.78, 0.8, 0.24, 8, rgb("#8FD3B8"), FONT_MONO, True)
textbox(s, "13 passed in 14.08s", 6.82, 3.22, 4.6, 0.3, 16, PAPER, FONT_MONO, True)
line(s, 6.82, 3.72, 12.2, 3.72, rgb("#2A4A3D"), 0.8)
textbox(s, "✓ GitHub Actions  ·  push / PR 自动执行", 6.82, 3.9, 5.2, 0.25, 8, rgb("#8FD3B8"), FONT_MONO)
textbox(s, "✓ 测试配置：临时 SQLite + 临时上传目录", 6.82, 4.25, 5.2, 0.25, 8, rgb("#AFC4B8"), FONT_MONO)
textbox(s, "✓ 测试环境 CSRF 关闭，生产开启", 6.82, 4.6, 5.2, 0.25, 8, rgb("#AFC4B8"), FONT_MONO)

textbox(s, "手工验收：双主题 / 响应式 / 编辑器 / 上传 / 权限", 0.92, 6.52, 11.5, 0.28, 9, MUTED, FONT_MONO, align=PP_ALIGN.CENTER)
add_notes(s, "我们没有只靠“点一遍”。项目有 13 个自动化测试，覆盖登录、越权、文章 CRUD、搜索、评论审核、收藏、XSS 过滤和图片上传，后台 13 个页面也有冒烟测试。GitHub Actions 在每次 push 和 PR 时自动跑，测试用独立 SQLite，不会碰演示数据。")

# =====================================================================
# 14 部署与协作
# =====================================================================
s = new_slide(number=14, section=SECTION_NAMES[14])
eyebrow(s, "13  /  DEPLOY & COLLABORATION")
title(s, "一条命令启动，五个人并行不打架")
subtitle(s, "Docker Compose + Gunicorn；简化 Git Flow + PR + CI。", w=5.2, size=11)

rect(s, 0.82, 1.95, 5.55, 2.55, CODEBG, None, radius=0.04)
textbox(s, "terminal", 1.04, 2.09, 1.0, 0.2, 6.8, rgb("#7F9B8B"), FONT_MONO)
textbox(s, "$ docker compose up -d --build", 1.04, 2.42, 4.9, 0.28, 9.5, rgb("#8FD3B8"), FONT_MONO, True)
textbox(s, "app   →  http://127.0.0.1:5000", 1.04, 2.86, 4.7, 0.25, 8, PAPER, FONT_MONO)
textbox(s, "mysql →  127.0.0.1:3307", 1.04, 3.16, 4.7, 0.25, 8, PAPER, FONT_MONO)
textbox(s, "首次启动：init-db  +  seed-demo", 1.04, 3.46, 4.7, 0.25, 8, rgb("#AFC4B8"), FONT_MONO)
textbox(s, "数据卷：mysql_data / uploads_data", 1.04, 3.76, 4.7, 0.25, 8, rgb("#AFC4B8"), FONT_MONO)
textbox(s, "自动建表  /  演示数据  /  图片持久化", 1.04, 4.93, 4.8, 0.24, 8, GREEN, FONT_MONO, True)

# 分支图
textbox(s, "BRANCH MODEL", 6.65, 1.72, 2.0, 0.22, 7, GREEN, FONT_MONO, True)
line(s, 6.72, 2.55, 12.2, 2.55, GREEN, 2.2)
line(s, 7.0, 3.15, 12.0, 3.15, TERRA, 1.6)
line(s, 7.7, 3.72, 11.4, 3.72, BLUE, 1.4)
for x, color in [(6.72, GREEN), (8.3, GREEN), (10.0, GREEN), (11.7, GREEN)]:
    dot(s, x - 0.055, 2.495, 0.11, color)
for x in [7.0, 8.5, 10.0, 11.5]:
    dot(s, x - 0.05, 3.1, 0.1, TERRA)
for x in [7.7, 9.2, 10.8]:
    dot(s, x - 0.045, 3.675, 0.09, BLUE)
textbox(s, "main", 11.85, 2.32, 0.6, 0.2, 7, GREEN, FONT_MONO, True)
textbox(s, "develop", 11.6, 2.93, 0.8, 0.2, 7, TERRA, FONT_MONO, True)
textbox(s, "feature/*", 10.75, 3.52, 0.9, 0.2, 7, BLUE, FONT_MONO, True)
textbox(s, "保护 + CI + 1 Approve", 6.7, 4.1, 3.1, 0.24, 8, MUTED, FONT_MONO)
textbox(s, "Squash merge", 9.9, 4.1, 1.5, 0.24, 8, MUTED, FONT_MONO)

# PR 规则
pill(s, "CI PASS", 6.7, 4.6, 0.95, LIGHTGREEN, GREEN, 7)
pill(s, "1 APPROVE", 7.8, 4.6, 1.1, PEACH, TERRA, 7)
pill(s, "SQUASH", 9.05, 4.6, 0.9, PALEBLUE, BLUE, 7)
pill(s, "PR TEMPLATE", 10.1, 4.6, 1.45, PAPER, INK, 7)
textbox(s, "提交规范：feat / fix / docs / style / refactor / test / chore", 6.7, 5.12, 5.4, 0.24, 7.5, MUTED, FONT_MONO)
textbox(s, "main 随时可演示  ·  develop 集成  ·  feature 短分支", 0.86, 6.45, 11.4, 0.28, 9, GREEN, FONT_MONO, True, align=PP_ALIGN.CENTER)
add_notes(s, "部署上提供 Docker Compose，一条命令启动 MySQL 和应用，首次自动建表并生成演示数据。协作上采用简化 Git Flow：main 保护、develop 集成、feature 短分支，提交遵循 Conventional Commits，PR 必须过 CI 和至少一人评审。这样五个人并行开发时，冲突和回滚都可控。")

# =====================================================================
# 15 成果与边界
# =====================================================================
s = new_slide(number=15, section=SECTION_NAMES[15])
eyebrow(s, "14  /  RETROSPECTIVE")
title(s, "成果与边界：我们完成了什么，还差什么")
subtitle(s, "不把“没做”说成“不需要”；明确取舍，也明确下一步。")

stats = [("9", "张数据表"), ("30+", "后端路由"), ("20+", "页面模板"), ("13", "自动化测试")]
for i, (num, label) in enumerate(stats):
    col, row = i % 2, i // 2
    x = 0.82 + col * 2.65
    y = 1.75 + row * 1.55
    rect(s, x, y, 2.42, 1.32, PAPER, LINE, radius=0.04)
    textbox(s, num, x + 0.2, y + 0.16, 1.8, 0.6, 30, GREEN, FONT_SERIF, True)
    textbox(s, label, x + 0.22, y + 0.86, 2.0, 0.24, 8.5, MUTED)

textbox(s, "已完成", 6.3, 1.72, 2.0, 0.28, 12, GREEN, FONT_BODY, True)
done = ["主体 5 项 + 扩展 6 项", "Markdown / 评论 / 收藏 / 上传", "数据看板 + 7 日趋势", "Docker + CI + 全套文档"]
for i, item in enumerate(done):
    y = 2.12 + i * 0.48
    textbox(s, "✓", 6.34, y, 0.22, 0.2, 8.5, GREEN, FONT_BODY, True)
    textbox(s, item, 6.62, y - 0.01, 4.6, 0.24, 8.8, SOFT)

textbox(s, "主动取舍", 6.3, 4.18, 2.0, 0.28, 12, TERRA, FONT_BODY, True)
limits = ["搜索仍用 LIKE，待全文索引", "单博主模型，未做多作者", "图片存本地，未接对象存储", "评论未做多级回复 / 邮件"]
for i, item in enumerate(limits):
    y = 4.58 + i * 0.48
    textbox(s, "→", 6.34, y, 0.22, 0.2, 8.5, TERRA, FONT_BODY, True)
    textbox(s, item, 6.62, y - 0.01, 4.8, 0.24, 8.8, MUTED)

textbox(s, "“不是没想到，而是课程周期内的主动取舍。”", 6.3, 6.35, 5.4, 0.3, 10, GREEN, FONT_SERIF, italic=True)
add_notes(s, "成果方面，我们完成了 9 张表、30 多个路由、20 多个页面，主体和扩展功能都能演示，测试和文档也齐全。也清楚不足：搜索还是 LIKE，数据量大要上全文索引；目前是单博主，没有多作者协作；图片存本地，生产可以换对象存储。这些不是“没想到”，而是课程周期内的主动取舍。")

# =====================================================================
# 16 总结
# =====================================================================
s = new_slide(DARKGREEN)
rect(s, 9.6, -1.1, 4.8, 4.8, RGBColor(0x1A, 0x55, 0x45), shape=MSO_SHAPE.OVAL)
rect(s, 11.1, 1.5, 2.4, 2.4, DARKGREEN, rgb("#2A7560"), shape=MSO_SHAPE.OVAL)
textbox(s, "KEEP GROWING", 0.92, 1.08, 4.0, 0.3, 9, rgb("#A9C1B4"), FONT_MONO, True)
textbox(s, "把零散的知识，\n收进一座会生长的小栈。", 0.88, 1.55, 8.6, 1.65, 34, PAPER, FONT_SERIF, True, line_spacing=1.35)
line(s, 0.92, 3.55, 3.3, 3.55, TERRA, 2)
textbox(s, "它是课程项目，也是一个愿意继续用下去的工具。", 0.92, 3.78, 7.4, 0.45, 14, rgb("#B9CDC2"), FONT_SERIF, italic=True)

future = [("01", "全文搜索与内容推荐"), ("02", "多作者协作与版本历史"), ("03", "对象存储与 HTTPS 部署")]
for i, (num, text) in enumerate(future):
    x = 0.92 + i * 3.85
    textbox(s, num, x, 5.15, 0.35, 0.22, 8, TERRA, FONT_MONO, True)
    textbox(s, text, x, 5.46, 3.3, 0.3, 11, PAPER, FONT_BODY)

textbox(s, "谢谢观看  ·  欢迎提问", 0.92, 6.35, 6.0, 0.38, 17, PAPER, FONT_SERIF, True)
textbox(s, "第 X 组  ·  2026  ·  Flask + MySQL 8.0", 0.94, 6.85, 5.7, 0.24, 8, rgb("#8FAE9D"), FONT_MONO)
textbox(s, "Q&A", 11.2, 6.4, 1.2, 0.44, 22, TERRA, FONT_MONO, True, align=PP_ALIGN.RIGHT)
add_notes(s, "最后用一句话总结：把零散的知识，收进一座会生长的小栈。它现在是一个能跑、能写、能互动的课程项目，也是我们愿意继续用下去的工具。谢谢大家，欢迎提问。")

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print(f"saved: {OUT}")
print(f"slides: {len(prs.slides)}")
