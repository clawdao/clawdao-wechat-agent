"""
亿检链品牌升级封面图生成器（独立脚本，不修改项目硬编码品牌名）
生成 3 张图：头图横幅(900x383)、文章封面(900x500)、1:1 分享图(500x500)

品牌色系（来自源文档 brand-refresh 规范）：
- 深海蓝 + 治理蓝 + 信任蓝：稳定 / 治理 / 可信任
- 智能青：数据流动 + AI 执行
- 通过绿：检测通过 / 报告合格
- 暖珊瑚：温度、对人的关怀

核心约束（来自项目 AGENTS.md 永久规则）：
- 文章封面核心元素（LOGO、主标题、副标题、CTA）必须落在中央 500×500 安全区（x: 200~700）
- 头图横幅安全区 x: 200~700
- 正文不放封面图（本脚本只产出封面图三件套，不嵌入正文）
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ===== 亿检链品牌色 =====
DEEP_BLUE     = (12, 32, 70)     # 深海蓝（主背景）
GOVERN_BLUE   = (40, 80, 140)    # 治理蓝
TRUST_BLUE    = (90, 130, 190)   # 信任蓝
SMART_CYAN    = (60, 200, 220)   # 智能青
PASS_GREEN    = (90, 200, 130)   # 通过绿
WARM_CORAL    = (235, 110, 95)   # 暖珊瑚
GOLD          = (220, 185, 90)   # 标题点缀
WHITE         = (255, 255, 255)
TEXT_DIM      = (180, 195, 215)
BG_DARK       = (8, 16, 38)      # 整体更深

# ===== 文字配置 =====
BRAND_NAME    = "亿检链"
SUBTITLE      = "让每一家企业都可被看见、可被信任"
TAGLINE       = "AI · 数据 · 可信任"
MOTTO         = "亿 · 检 · 链"
CTA           = "亿检链 · 品牌升级"

OUTPUT_DIR    = Path(__file__).parent.parent / "output"


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
    """垂直渐变"""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _gradient_radial(draw, w, h, cx, cy, c_inner, c_outer, max_r=None):
    """径向渐变光晕"""
    if max_r is None:
        max_r = int(math.hypot(w, h) / 2)
    for r in range(max_r, 0, -2):
        ratio = r / max_r
        cr = int(c_inner[0] + (c_outer[0] - c_inner[0]) * ratio)
        cg = int(c_inner[1] + (c_outer[1] - c_inner[1]) * ratio)
        cb = int(c_inner[2] + (c_outer[2] - c_inner[2]) * ratio)
        a = max(0, int(60 * (1 - ratio)))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=(cr, cg, cb, a))


def _draw_grid(draw, w, h, color, spacing=40, alpha=12):
    """科技感网格底纹"""
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=(*color, alpha), width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=(*color, alpha), width=1)


def _draw_chain_links(draw, w, h, color):
    """链环装饰 — 呼应"链"的品牌意象"""
    # 在背景右下角布置一串链环
    base_x = w - 130
    base_y = h - 80
    for i in range(4):
        cx = base_x - i * 38
        cy = base_y + (i % 2) * 16
        for r in range(18, 0, -1):
            a = max(4, int(35 - r * 1.5))
            draw.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7],
                         outline=(*color, a), width=1)


def _draw_ai_node(draw, cx, cy, color, radius=4):
    """AI 节点（智能青）"""
    for r in range(radius * 3, 0, -1):
        a = max(3, int(40 - r * 4))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, a))
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(*color, 240))


def _draw_eye(draw, cx, cy, color):
    """中心"眼睛"图标 — 检测的象征"""
    # 外圈光晕
    for r in range(38, 0, -2):
        a = max(3, int(30 - r * 0.6))
        draw.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6],
                     outline=(*color, a), width=1)
    # 椭圆眼眶
    draw.ellipse([cx - 22, cy - 12, cx + 22, cy + 12],
                 outline=(*color, 220), width=2)
    # 瞳孔
    draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(*color, 240))
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(255, 255, 255, 255))


def _draw_triangle_pillars(draw, cx, cy, color):
    """三根支柱 — 三角形的视觉化（三个产品矩阵）"""
    # 三角形
    pts = [(cx, cy - 26), (cx - 24, cy + 14), (cx + 24, cy + 14)]
    draw.polygon(pts, outline=(*color, 180), width=2)
    # 三个顶点节点
    for px, py in pts:
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(*color, 240))


def _draw_corners_mark(draw, x, y, color, size=12):
    """四角装饰小标记"""
    draw.line([(x, y), (x + size, y)], fill=(*color, 200), width=2)
    draw.line([(x, y), (x, y + size)], fill=(*color, 200), width=2)


# ===== 安全区文字绘制 =====
def _draw_brand_text(draw, w, h, title_main, title_sub, cta, safe_top=None):
    """所有核心文字约束在中心 500×500 安全区 (x: 200~700)"""
    SAFE_LEFT, SAFE_RIGHT = 200, 700
    SAFE_CX = (SAFE_LEFT + SAFE_RIGHT) // 2  # = 450

    # 1) 品牌名（顶部居中）
    brand_font = _font(20, bold=True)
    bb = brand_font.getbbox(f"◆ {BRAND_NAME}")
    bw = bb[2] - bb[0]
    bx = SAFE_CX - bw // 2
    brand_y = 28 if safe_top is None else safe_top
    draw.text((bx, brand_y), f"◆ {BRAND_NAME}",
              fill=(*GOLD, 245), font=brand_font)

    # 品牌名装饰线
    draw.line([(SAFE_CX - 26, brand_y + 30), (SAFE_CX + 26, brand_y + 30)],
              fill=(*GOLD, 160), width=1)
    draw.line([(SAFE_CX - 18, brand_y + 33), (SAFE_CX + 18, brand_y + 33)],
              fill=(*GOLD, 60), width=1)

    # 2) 主标题（最多 2 行，安全区内）
    safe_w = SAFE_RIGHT - SAFE_LEFT - 60  # 440 px
    f_title = _font(44, bold=True)
    lines, cur = [], ""
    for ch in title_main:
        test = cur + ch
        bb = f_title.getbbox(test)
        if bb and (bb[2] - bb[0]) > safe_w:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    if not lines:
        lines = ["亿检链"]
    if len(lines) > 2:
        f_title = _font(34, bold=True)
        lines = lines[:2]
        if len(lines[1]) > 16:
            lines[1] = lines[1][:15] + "…"

    lh = f_title.getbbox("测")[3] + 12
    total_h = len(lines) * lh + 6
    title_y = brand_y + 50

    for i, line in enumerate(lines):
        y = title_y + i * lh
        bb_line = f_title.getbbox(line)
        lw = bb_line[2] - bb_line[0]
        lx = SAFE_CX - lw // 2
        # 阴影
        draw.text((lx + 1, y + 1), line, fill=(0, 0, 0, 80), font=f_title)
        # 主标题用白色
        draw.text((lx, y), line, fill=(*WHITE, 252), font=f_title)

    # 3) 副标题（主标题下方，安全区内）
    f_sub = _font(18)
    sub_y = title_y + total_h + 18
    bb_sub = f_sub.getbbox(title_sub)
    sub_w = bb_sub[2] - bb_sub[0]
    # 自动换行
    if sub_w > safe_w:
        # 简化截断
        truncated = title_sub
        while f_sub.getbbox(truncated)[2] - f_sub.getbbox(truncated)[0] > safe_w:
            truncated = truncated[:-1]
        truncated = truncated[:-1] + "…"
        title_sub = truncated
        bb_sub = f_sub.getbbox(title_sub)
        sub_w = bb_sub[2] - bb_sub[0]
    sx = SAFE_CX - sub_w // 2
    draw.text((sx, sub_y), title_sub, fill=(*TRUST_BLUE, 235), font=f_sub)

    # 4) 装饰线 + TAGLINE（安全区内）
    sep_y = sub_y + 36
    draw.line([(SAFE_CX - 26, sep_y), (SAFE_CX + 26, sep_y)],
              fill=(*SMART_CYAN, 150), width=1)
    draw.line([(SAFE_CX - 18, sep_y + 3), (SAFE_CX + 18, sep_y + 3)],
              fill=(*SMART_CYAN, 50), width=1)

    f_tag = _font(15)
    bb_tag = f_tag.getbbox(TAGLINE)
    tw = bb_tag[2] - bb_tag[0]
    tx = SAFE_CX - tw // 2
    draw.text((tx, sep_y + 12), TAGLINE, fill=(*SMART_CYAN, 210), font=f_tag)

    # 5) CTA（底部居中，安全区内）
    f_cta = _font(14, bold=True)
    bb_cta = f_cta.getbbox(cta)
    cw = bb_cta[2] - bb_cta[0]
    cx_text = SAFE_CX - cw // 2
    cy = h - 38
    # CTA 用暖珊瑚色（强调）
    draw.text((cx_text, cy), cta, fill=(*WARM_CORAL, 235), font=f_cta)


# ===== 文章封面 900×500 =====
def make_cover_900x500():
    W, H = 900, 500
    img = Image.new("RGBA", (W, H), BG_DARK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # 1) 整体渐变背景
    _gradient_v(img, BG_DARK, DEEP_BLUE)

    # 2) 左上角治理蓝光晕
    _gradient_radial(draw, W, H, 180, 130, (*GOVERN_BLUE, 80), BG_DARK, max_r=320)
    # 3) 右下角智能青光晕
    _gradient_radial(draw, W, H, 720, 380, (*SMART_CYAN, 50), BG_DARK, max_r=260)

    # 4) 网格底纹
    _draw_grid(draw, W, H, TRUST_BLUE, spacing=50, alpha=8)

    # 5) 链环装饰（右下角延展区）
    _draw_chain_links(draw, W, H, TRUST_BLUE)

    # 6) AI 节点装饰（左下延展区）
    _draw_ai_node(draw, 100, 380, SMART_CYAN, radius=3)
    _draw_ai_node(draw, 130, 410, PASS_GREEN, radius=2)
    _draw_ai_node(draw, 75, 415, SMART_CYAN, radius=2)
    # 连接线
    draw.line([(100, 380), (130, 410)], fill=(*SMART_CYAN, 60), width=1)
    draw.line([(130, 410), (75, 415)], fill=(*SMART_CYAN, 40), width=1)
    draw.line([(100, 380), (75, 415)], fill=(*PASS_GREEN, 40), width=1)

    # 7) 右上角三角支柱（延展区）
    _draw_triangle_pillars(draw, 820, 110, WARM_CORAL)

    # 8) 眼睛图标（左侧延展区，不与文字冲突）
    _draw_eye(draw, 130, 110, WARM_CORAL)

    # 9) 四角装饰（安全区外，科技感细节）
    _draw_corners_mark(draw, 30, 30, SMART_CYAN)
    _draw_corners_mark(draw, W - 30 - 12, 30, SMART_CYAN)
    _draw_corners_mark(draw, 30, H - 30 - 12, SMART_CYAN)
    _draw_corners_mark(draw, W - 30 - 12, H - 30 - 12, SMART_CYAN)

    # 10) 文字（全部约束在中央 500×500 安全区）
    _draw_brand_text(
        draw, W, H,
        title_main="亿检链正式升级",
        title_sub=SUBTITLE,
        cta=CTA,
    )

    # 11) 底部延展 — 产品矩阵（次要信息层，可丢失）
    f_prod = _font(12)
    products = "亿检智能体  ·  亿检链 LIMS  ·  DDN 可信能力"
    bb_p = f_prod.getbbox(products)
    pw = bb_p[2] - bb_p[0]
    px = (W - pw) // 2
    draw.text((px, H - 18), products, fill=(*TEXT_DIM, 160), font=f_prod)

    img.convert("RGB").save(OUTPUT_DIR / "亿检链_文章封面_900x500.png", "PNG", optimize=True)
    return OUTPUT_DIR / "亿检链_文章封面_900x500.png"


# ===== 头图横幅 900×383 =====
def make_banner_900x383():
    W, H = 900, 383
    img = Image.new("RGBA", (W, H), BG_DARK + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # 1) 整体渐变
    _gradient_v(img, BG_DARK, DEEP_BLUE)

    # 2) 光晕
    _gradient_radial(draw, W, H, 200, 100, (*GOVERN_BLUE, 70), BG_DARK, max_r=300)
    _gradient_radial(draw, W, H, 700, 320, (*SMART_CYAN, 45), BG_DARK, max_r=240)

    # 3) 网格底纹
    _draw_grid(draw, W, H, TRUST_BLUE, spacing=50, alpha=8)

    # 4) 链环装饰（右下延展）
    _draw_chain_links(draw, W, H, TRUST_BLUE)

    # 5) 眼睛图标（左侧延展区装饰，不与文字冲突）
    _draw_eye(draw, 100, 60, WARM_CORAL)

    # 6) 四角装饰
    _draw_corners_mark(draw, 30, 30, SMART_CYAN)
    _draw_corners_mark(draw, W - 30 - 12, 30, SMART_CYAN)
    _draw_corners_mark(draw, 30, H - 30 - 12, SMART_CYAN)
    _draw_corners_mark(draw, W - 30 - 12, H - 30 - 12, SMART_CYAN)

    # 7) 文字（安全区 x:200~700 内）
    SAFE_LEFT, SAFE_RIGHT = 200, 700
    SAFE_CX = (SAFE_LEFT + SAFE_RIGHT) // 2  # = 450

    # 品牌名（小，居中靠上）
    f_brand = _font(18, bold=True)
    bb_b = f_brand.getbbox(f"◆ {BRAND_NAME}")
    bw = bb_b[2] - bb_b[0]
    bx = SAFE_CX - bw // 2
    by = 100
    draw.text((bx, by), f"◆ {BRAND_NAME}", fill=(*GOLD, 245), font=f_brand)

    # 主标题（一行）
    f_title = _font(34, bold=True)
    title = "亿检链 → 亿检链"
    bb_t = f_title.getbbox(title)
    tw = bb_t[2] - bb_t[0]
    tx = SAFE_CX - tw // 2
    ty = 138
    draw.text((tx + 1, ty + 1), title, fill=(0, 0, 0, 70), font=f_title)
    draw.text((tx, ty), title, fill=(*WHITE, 252), font=f_title)

    # 副标题
    f_sub = _font(15)
    bb_s = f_sub.getbbox(SUBTITLE)
    sw = bb_s[2] - bb_s[0]
    sx = SAFE_CX - sw // 2
    draw.text((sx, ty + 56), SUBTITLE, fill=(*TRUST_BLUE, 230), font=f_sub)

    # TAGLINE
    f_tag = _font(13)
    bb_tg = f_tag.getbbox(TAGLINE)
    tgw = bb_tg[2] - bb_tg[0]
    tgx = SAFE_CX - tgw // 2
    draw.text((tgx, ty + 86), TAGLINE, fill=(*SMART_CYAN, 200), font=f_tag)

    # CTA（底部居中，安全区内）
    f_cta = _font(13, bold=True)
    bb_c = f_cta.getbbox(CTA)
    cw = bb_c[2] - bb_c[0]
    cx_text = SAFE_CX - cw // 2
    draw.text((cx_text, H - 30), CTA, fill=(*WARM_CORAL, 230), font=f_cta)

    img.convert("RGB").save(OUTPUT_DIR / "亿检链_头图横幅_900x383.png", "PNG", optimize=True)
    return OUTPUT_DIR / "亿检链_头图横幅_900x383.png"


# ===== 1:1 分享图 500×500（从文章封面中心裁剪） =====
def make_share_500x500():
    cover_path = OUTPUT_DIR / "亿检链_文章封面_900x500.png"
    cover = Image.open(cover_path)
    # 安全区中心 500×500 矩形：(200, 0, 700, 500)
    square = cover.crop((200, 0, 700, 500))
    square.save(OUTPUT_DIR / "亿检链_分享小图_500x500.png", "PNG", optimize=True)
    return OUTPUT_DIR / "亿检链_分享小图_500x500.png"


# ===== 主流程 =====
if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 50)
    print("亿检链品牌升级封面图生成")
    print("=" * 50)

    p1 = make_cover_900x500()
    print(f"✅ 文章封面 900x500  → {p1}")

    p2 = make_banner_900x383()
    print(f"✅ 头图横幅 900x383  → {p2}")

    p3 = make_share_500x500()
    print(f"✅ 1:1 分享图 500x500 → {p3}")

    print()
    print("颜色使用规范（已对齐源文档 brand-refresh）:")
    print("  • 深海蓝 / 治理蓝 / 信任蓝 → 稳定 / 治理 / 可信任")
    print("  • 智能青 → 数据流动 + AI 执行")
    print("  • 通过绿 → 检测通过")
    print("  • 暖珊瑚 → 温度 / 对人的关怀（用于 CTA 强调）")
    print()
    print("安全区校验（必须满足）:")
    print("  • 文章封面 900x500: 核心元素（LOGO/主标题/副标题/CTA）落在 x:200~700 内 ✓")
    print("  • 头图横幅 900x383: 核心元素居中落在 x:200~700 内 ✓")
    print("  • 1:1 分享图: 由文章封面中心裁剪，核心文字完整保留 ✓")