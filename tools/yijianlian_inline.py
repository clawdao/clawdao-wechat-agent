"""
亿检链文章内嵌插图生成器
替代源文档 SVG（market-overview.svg / market-lims-cycle.svg）
所有插图严格对齐亿检链品牌色系，安全区遵守项目规范
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ===== 品牌色 =====
DEEP_BLUE     = (12, 32, 70)
GOVERN_BLUE   = (40, 80, 140)
TRUST_BLUE    = (90, 130, 190)
SMART_CYAN    = (60, 200, 220)
PASS_GREEN    = (90, 200, 130)
WARM_CORAL    = (235, 110, 95)
GOLD          = (220, 185, 90)
WHITE         = (255, 255, 255)
TEXT_DIM      = (180, 195, 215)
TEXT_BODY     = (235, 235, 240)
BG_DARK       = (8, 16, 38)

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "inline_yijianlian"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _font(size: int, bold: bool = False):
    paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _gradient_v(img, c1, c2):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _gradient_radial(draw, w, h, cx, cy, c_inner, c_outer, max_r=None):
    if max_r is None:
        max_r = int(math.hypot(w, h) / 2)
    for r in range(max_r, 0, -2):
        ratio = r / max_r
        cr = int(c_inner[0] + (c_outer[0] - c_inner[0]) * ratio)
        cg = int(c_inner[1] + (c_outer[1] - c_inner[1]) * ratio)
        cb = int(c_inner[2] + (c_outer[2] - c_inner[2]) * ratio)
        a = max(0, int(50 * (1 - ratio)))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(cr, cg, cb, a))


def _draw_grid(draw, w, h, color, spacing=40, alpha=8):
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=(*color, alpha), width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=(*color, alpha), width=1)


def _text_center(draw, text, y, font, color, w):
    bb = font.getbbox(text)
    tw = bb[2] - bb[0]
    draw.text(((w - tw) // 2, y), text, fill=color, font=font)


# ===== 插图 1：品牌架构 =====
def make_brand_overview():
    """替代源文档 market-overview.svg — 亿检链四层品牌架构图
    重写：使用深色卡片底 + 纯白文字，提升对比度"""
    W, H = 1200, 800
    img = Image.new("RGBA", (W, H), BG_DARK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # 背景
    _gradient_v(img, BG_DARK, DEEP_BLUE)
    _gradient_radial(draw, W, H, 220, 220, (*GOVERN_BLUE, 60), BG_DARK, max_r=420)
    _gradient_radial(draw, W, H, 980, 580, (*SMART_CYAN, 40), BG_DARK, max_r=400)
    _draw_grid(draw, W, H, TRUST_BLUE, spacing=60, alpha=6)

    # ===== 顶部标题区 =====
    _text_center(draw, "利姆斯科技旗下品牌 · LIMSCHAIN BRAND ARCHITECTURE",
                 30, _font(16), TRUST_BLUE, W)
    _text_center(draw, "亿检链 · 品牌架构", 60, _font(36, bold=True), WHITE, W)
    _text_center(draw, "L · I · M · S", 108, _font(22, bold=True), GOLD, W)

    # ===== 顶部母品牌卡片（横跨宽度）=====
    card_top = 165
    card_h = 130
    # 主卡片 — 用深色底 + 金色边
    draw.rounded_rectangle(
        [W // 2 - 500, card_top, W // 2 + 500, card_top + card_h],
        radius=12, fill=(15, 25, 55, 240), outline=(*GOLD, 230), width=3
    )
    # 内描边（装饰）
    draw.rounded_rectangle(
        [W // 2 - 495, card_top + 5, W // 2 + 495, card_top + card_h - 5],
        radius=10, outline=(*GOLD, 60), width=1
    )
    # 主品牌名
    f_mb_brand = _font(32, bold=True)
    _text_center(draw, "● 亿检链 · 母品牌", card_top + 18, f_mb_brand, GOLD, W)
    f_mb_label = _font(15)
    _text_center(draw, "LIMSCHAIN · 利姆斯科技旗下",
                 card_top + 65, f_mb_label, WHITE, W)
    _text_center(draw, "在人工智能发展的大潮里，助力企业成为 AI Native",
                 card_top + 90, f_mb_label, TRUST_BLUE, W)

    # 三个连接线（垂直线 + 圆点）
    connector_y = card_top + card_h + 4
    for cx in [W // 2 - 280, W // 2, W // 2 + 280]:
        draw.line([(cx, connector_y), (cx, connector_y + 30)],
                  fill=(*GOLD, 160), width=2)
        draw.ellipse([cx - 5, connector_y + 30, cx + 5, connector_y + 40],
                     fill=(*GOLD, 230))

    # ===== 三个子品牌卡片（深底 + 强对比）=====
    sub_y = connector_y + 55
    sub_h = 270
    card_w = 360
    cards = [
        {
            "color": SMART_CYAN,
            "name": "亿检智能体",
            "en": "AI AGENTS",
            "desc": "帮你做事的数字员工",
            "spec": "读报告 · 审合同 · 盯流程 · 答问题",
        },
        {
            "color": WARM_CORAL,
            "name": "亿检链 LIMS",
            "en": "LAB INFORMATION MGMT",
            "desc": "让实验室跑起来",
            "spec": "样本 · 数据 · 报告 · 全流程可追溯",
        },
        {
            "color": PASS_GREEN,
            "name": "DDN 可信能力",
            "en": "DATA DELIVERY NETWORK",
            "desc": "让数据可信任、可追溯",
            "spec": "DDN 可信区块链 · 不可篡改 · 可解释",
        },
    ]
    for i, c in enumerate(cards):
        # 三张子卡宽度 360，间距 20，需要总宽 3*360 + 2*20 = 1120，刚好填满
        cx = (card_w // 2) + i * (card_w + 20)  # 180, 560, 940
        x0 = cx - card_w // 2
        x1 = cx + card_w // 2
        # 卡片底（深底色 + 彩色边）
        draw.rounded_rectangle(
            [x0, sub_y, x1, sub_y + sub_h],
            radius=12, fill=(15, 25, 55, 240), outline=(*c["color"], 220), width=3
        )
        # 顶部色条
        draw.rectangle([x0 + 4, sub_y + 4, x1 - 4, sub_y + 14],
                       fill=(*c["color"], 220))
        # 名称（白色 + 大字 + 黑阴影）
        f_name = _font(26, bold=True)
        bb = f_name.getbbox(c["name"])
        nw = bb[2] - bb[0]
        draw.text((cx - nw // 2 + 1, sub_y + 33), c["name"], fill=(0, 0, 0, 200), font=f_name)
        draw.text((cx - nw // 2, sub_y + 32), c["name"], fill=WHITE + (255,), font=f_name)
        # 英文小标（卡片色）
        f_en = _font(12)
        bb = f_en.getbbox(c["en"])
        ew = bb[2] - bb[0]
        draw.text((cx - ew // 2, sub_y + 68), c["en"],
                  fill=(*c["color"], 230), font=f_en)
        # 分隔线
        draw.line([(x0 + 50, sub_y + 95), (x1 - 50, sub_y + 95)],
                  fill=(*c["color"], 140), width=1)
        # 描述（白色加粗）
        f_desc = _font(18, bold=True)
        bb = f_desc.getbbox(c["desc"])
        dw_ = bb[2] - bb[0]
        draw.text((cx - dw_ // 2, sub_y + 110), c["desc"],
                  fill=WHITE + (250,), font=f_desc)
        # 细节（柔和白）
        f_spec = _font(14)
        bb = f_spec.getbbox(c["spec"])
        sw = bb[2] - bb[0]
        draw.text((cx - sw // 2, sub_y + 152), c["spec"],
                  fill=TEXT_BODY + (230,), font=f_spec)
        # 底部装饰小点
        for j in range(5):
            draw.ellipse(
                [x0 + 40 + j * 14, sub_y + sub_h - 30,
                 x0 + 40 + j * 14 + 4, sub_y + sub_h - 26],
                fill=(*c["color"], 170)
            )

    # ===== 底部标签 =====
    bottom_y = H - 50
    draw.line([(60, bottom_y - 18), (W - 60, bottom_y - 18)],
              fill=(*TRUST_BLUE, 80), width=1)
    _text_center(draw, "三类客户价值 · 让数智化慢慢长出来",
                 bottom_y, _font(15, bold=True), GOLD, W)
    _text_center(draw, "01 获客运营  ·  02 内部管理  ·  03 研发落地",
                 bottom_y + 22, _font(12), TEXT_DIM, W)

    out = OUTPUT_DIR / "brand-overview.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    return out


# ===== 插图 2：LIMS 闭环 =====
def make_lims_cycle():
    """替代源文档 market-lims-cycle.svg — LIMS 闭环关系图
    重写：中央上下结构 + 四节点横向排列，避免重叠"""
    W, H = 1200, 760
    img = Image.new("RGBA", (W, H), BG_DARK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    _gradient_v(img, BG_DARK, DEEP_BLUE)
    _gradient_radial(draw, W, H, 600, 350, (*GOVERN_BLUE, 60), BG_DARK, max_r=500)
    _gradient_radial(draw, W, H, 200, 350, (*SMART_CYAN, 35), BG_DARK, max_r=300)
    _gradient_radial(draw, W, H, 1000, 350, (*WARM_CORAL, 30), BG_DARK, max_r=300)
    _draw_grid(draw, W, H, TRUST_BLUE, spacing=60, alpha=5)

    # 顶部标题
    _text_center(draw, "LIMS 闭环 · 经营确定性公式",
                 35, _font(34, bold=True), WHITE, W)
    _text_center(draw, "从「检测」到「追溯」— 让企业的每一项关键业务都可被验证",
                 78, _font(15), TRUST_BLUE, W)

    # ===== 中央核心（较小）=====
    cx = W // 2
    cy = 380
    # 中心圆环（外圈）
    for r in range(75, 0, -2):
        ratio = r / 75
        a = int(40 * (1 - ratio))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=(*GOLD, a), width=1)
    # 中心填充圆
    draw.ellipse([cx - 55, cy - 55, cx + 55, cy + 55],
                 fill=(20, 30, 60, 245), outline=(*GOLD, 230), width=3)
    # LIMS 大字
    f_big = _font(30, bold=True)
    _text_center(draw, "LIMS", cy - 35, f_big, GOLD, W)
    _text_center(draw, "经营确定性", cy + 0, _font(12, bold=True), WHITE, W)
    _text_center(draw, "可检测 · 可决策", cy + 18, _font(9), TEXT_BODY, W)
    _text_center(draw, "可执行 · 可追溯", cy + 30, _font(9), TEXT_BODY, W)

    # ===== 四个节点（上下左右交叉）=====
    node_r = 60
    nodes = [
        {
            "pos": (cx, 220),
            "letter": "L",
            "title": "检测",
            "en": "LOCATE",
            "desc": ["看见问题在哪", "知道数据来自哪"],
            "spec": ["采集 · 标识 · 接入", "质量检测 · 信号发现"],
            "color": SMART_CYAN,
        },
        {
            "pos": (cx - 360, cy),
            "letter": "I",
            "title": "决策",
            "en": "INTERPRET",
            "desc": ["把看见的东西读懂", "告诉业务意味着什么"],
            "spec": ["亿检智能体 · 分析报告", "规则判断 · AI 解读"],
            "color": WARM_CORAL,
        },
        {
            "pos": (cx, cy + 280),
            "letter": "M",
            "title": "执行",
            "en": "MOBILIZE",
            "desc": ["把决策变成动作", "让流程自动跑起来"],
            "spec": ["流程自动化 · 任务编排", "触发器 · 审批流"],
            "color": PASS_GREEN,
        },
        {
            "pos": (cx + 360, cy),
            "letter": "S",
            "title": "追溯",
            "en": "SUSTAIN",
            "desc": ["每一份结果都留得住", "每一份证据都查得回"],
            "spec": ["DDN 可信区块链 · 不可篡改", "审计 · 合规 · 解释"],
            "color": GOLD,
        },
    ]

    # 先画连接箭头（在节点之下）
    arrow_pairs = [
        # (起点, 终点, 起点色, 终点色) — 从节点边缘出发到下一节点边缘
        ((cx - 65, 250), (cx - 270, cy - 40), SMART_CYAN, WARM_CORAL),   # L→I
        ((cx - 270, cy + 40), (cx - 65, cy + 210), WARM_CORAL, PASS_GREEN),# I→M
        ((cx + 65, cy + 210), (cx + 270, cy + 40), PASS_GREEN, GOLD),     # M→S
        ((cx + 270, cy - 40), (cx + 65, 250), GOLD, SMART_CYAN),          # S→L
    ]
    for (x0, y0), (x1, y1), col1, col2 in arrow_pairs:
        # 画弧形虚线箭头
        for t in range(0, 100, 3):
            t01 = t / 100
            ax = x0 + (x1 - x0) * t01
            ay = y0 + (y1 - y0) * t01
            # 弧形偏移
            bx = ax + 25 * math.sin(t01 * math.pi)
            by = ay - 20 * math.sin(t01 * math.pi)
            cr = int(col1[0] * (1 - t01) + col2[0] * t01)
            cg = int(col1[1] * (1 - t01) + col2[1] * t01)
            cb = int(col1[2] * (1 - t01) + col2[2] * t01)
            draw.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=(cr, cg, cb, 200))

    # 画四个节点（圆形 + 字母 + 标题 + 描述）
    for n in nodes:
        nx, ny = n["pos"]
        # 节点外圈光晕
        for r in range(node_r + 35, node_r, -3):
            ratio = (r - node_r) / 35
            a = int(70 * (1 - ratio))
            draw.ellipse([nx - r, ny - r, nx + r, ny + r],
                         outline=(*n["color"], a), width=1)
        # 节点底圆（深色填充 + 彩色边）
        draw.ellipse([nx - node_r, ny - node_r, nx + node_r, ny + node_r],
                     fill=(20, 30, 60, 245), outline=(*n["color"], 230), width=3)

        # 节点内部：顶部字母，标题+描述+spec
        f_letter = _font(34, bold=True)
        bb = f_letter.getbbox(n["letter"])
        lw = bb[2] - bb[0]
        # 字母在节点上部 (ny - 42)
        draw.text((nx - lw // 2 + 1, ny - 42 + 1), n["letter"],
                  fill=(0, 0, 0, 200), font=f_letter)
        draw.text((nx - lw // 2, ny - 42), n["letter"],
                  fill=(*n["color"], 255), font=f_letter)

        # 标题（节点内部中上部，字母下方）
        f_t = _font(14, bold=True)
        bb = f_t.getbbox(n["title"])
        tw = bb[2] - bb[0]
        draw.text((nx - tw // 2, ny - 6), n["title"],
                  fill=WHITE + (255,), font=f_t)

        # 描述（节点内部中部）
        f_desc = _font(9)
        for j, line in enumerate(n["desc"]):
            bb = f_desc.getbbox(line)
            dw_ = bb[2] - bb[0]
            if dw_ > node_r * 2 - 6:
                while dw_ > node_r * 2 - 6:
                    line = line[:-1]
                    bb = f_desc.getbbox(line)
                    dw_ = bb[2] - bb[0]
                line = line[:-1] + "…"
                bb = f_desc.getbbox(line)
                dw_ = bb[2] - bb[0]
            draw.text((nx - dw_ // 2, ny + 14 + j * 12), line,
                      fill=TEXT_BODY + (220,), font=f_desc)

        # spec（节点内部底部，节点色小字）
        f_spec = _font(8)
        for j, line in enumerate(n["spec"]):
            bb = f_spec.getbbox(line)
            sw = bb[2] - bb[0]
            if sw > node_r * 2 - 6:
                while sw > node_r * 2 - 6:
                    line = line[:-1]
                    bb = f_spec.getbbox(line)
                    sw = bb[2] - bb[0]
                line = line[:-1] + "…"
                bb = f_spec.getbbox(line)
                sw = bb[2] - bb[0]
            draw.text((nx - sw // 2, ny + 40 + j * 11), line,
                      fill=(*n["color"], 200), font=f_spec)

    # 底部 caption
    draw.line([(80, H - 50), (W - 80, H - 50)],
              fill=(*TRUST_BLUE, 80), width=1)
    _text_center(draw, "L · I · M · S — 每家企业都能用，每项业务都能跑",
                 H - 22, _font(15, bold=True), GOLD, W)

    out = OUTPUT_DIR / "lims-cycle.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    return out


if __name__ == "__main__":
    print("=" * 60)
    print("亿检链内嵌插图生成（替代源 SVG）")
    print("=" * 60)

    p1 = make_brand_overview()
    print(f"✅ 品牌架构图: {p1} ({p1.stat().st_size // 1024} KB)")

    p2 = make_lims_cycle()
    print(f"✅ LIMS 闭环图: {p2} ({p2.stat().st_size // 1024} KB)")

    print()
    print("内容来源映射:")
    print("  • brand-overview.png ← source: market-overview.svg")
    print("  • lims-cycle.png     ← source: market-lims-cycle.svg")
    print("  • 不生成 market-hero.svg（封面图，按规则不放正文）")
    print("  • 不生成 LIMS-logo.png（Logo 重复，正文不需要）")