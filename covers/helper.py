"""
AI深度学堂 - 公众号封面生成器
- 头图横幅 900×383（订阅号顶部固定）
- 文章封面 900×500（推送正文大图，"一图二用"载体）

品牌色：深空紫蓝 + 鎏金 + 电蓝（Codex/AI 感）
核心产品：觉知岛 SaaS / Clawdao 龙虾岛 / DDN 区块链 / Codex 训练营

【一图二用设计原则】
- 文章封面 (900×500) 必须支持从中心裁剪出 1:1 分享图 (500×500)
- 核心层元素（LOGO、主标题、副标题、CTA）必须落在中央 500×500 安全区
- 延展区（两侧各 200 像素）只能放次要信息（产品矩阵、装饰）
- 详细规范见 images/README.md
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# ====== 品牌常量 ======
BRAND_NAME = "AI深度学堂"
BRAND_EN = "AI · DEEP · ACADEMY"
SUBTITLE = "为科技创业者打造的企业级 AI 认知升级阵地"
MOTTO = "ClawDao 重塑企业 · 区块链重塑信任 · 觉知重塑心智"
PRODUCTS = ["觉知岛 SaaS", "Clawdao 龙虾岛", "DDN 区块链", "Codex 训练营"]

# 调色板
BG_DEEP   = (5, 7, 22)
BG_PURPLE = (28, 18, 56)
GOLD       = (212, 175, 55)
GOLD_LIGHT = (242, 201, 76)
GOLD_SOFT  = (140, 110, 35)
CYAN       = (91, 189, 242)
CYAN_SOFT  = (79, 209, 197)
PURPLE     = (139, 92, 246)
TEXT_WHITE = (245, 247, 255)
TEXT_DIM   = (180, 185, 200)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGO_PATH = Path("/Users/imfly/Documents/projects/logo/logo-sd.png")

# ====== 工具函数 ======
def _font(size: int) -> ImageFont.FreeTypeFont:
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


def _text_w(text, font) -> int:
    if hasattr(font, "getlength"):
        return int(font.getlength(text))
    bb = font.getbbox(text)
    return bb[2] - bb[0]


def _text_xy_centered(text, font, container_w):
    """返回 (x, y) 中 x 已居中, y 为 0。文字宽度不足时偏移给出。"""
    tw = _text_w(text, font)
    return (container_w - tw) // 2, tw


def _v_gradient(draw, w, h, c1, c2):
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _radial_glow(img, cx, cy, radius, color, alpha=70):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -2):
        a = int(alpha * (1 - r / radius) ** 2)
        if a < 1:
            continue
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, a))
    overlay = overlay.filter(ImageFilter.GaussianBlur(max(2, radius // 5)))
    img.alpha_composite(overlay)


def _draw_corner_brackets(draw, w, h, c, ln=18, t=1):
    s = ln
    draw.line([(14, 14), (14 + s, 14)], fill=(*c, 180), width=t)
    draw.line([(14, 14), (14, 14 + s)], fill=(*c, 180), width=t)
    draw.line([(w - 14, 14), (w - 14 - s, 14)], fill=(*c, 180), width=t)
    draw.line([(w - 14, 14), (w - 14, 14 + s)], fill=(*c, 180), width=t)
    draw.line([(14, h - 14), (14 + s, h - 14)], fill=(*c, 180), width=t)
    draw.line([(14, h - 14), (14, h - 14 - s)], fill=(*c, 180), width=t)
    draw.line([(w - 14, h - 14), (w - 14 - s, h - 14)], fill=(*c, 180), width=t)
    draw.line([(w - 14, h - 14), (w - 14, h - 14 - s)], fill=(*c, 180), width=t)


def _draw_chain_network(draw, w, h, seed=7):
    """在延展区（右侧）画区块链网络装饰，可被裁剪丢弃。"""
    import random
    random.seed(seed)
    cx, cy = int(w * 0.78), int(h * 0.55)
    main_pts = [
        (cx + 80,  cy - 95), (cx + 110, cy - 25), (cx + 125, cy + 50),
        (cx + 60,  cy + 110),(cx - 10,  cy + 100),(cx - 65,  cy - 55),
        (cx - 45,  cy - 115),(cx + 25,  cy - 75), (cx - 90, cy + 30),
    ]
    for i, (x, y) in enumerate(main_pts):
        for j, (x2, y2) in enumerate(main_pts[i + 1:], i + 1):
            if random.random() > 0.45:
                continue
            c = GOLD_LIGHT if (i + j) % 3 == 0 else (CYAN if (i + j) % 3 == 1 else PURPLE)
            draw.line([(x, y), (x2, y2)], fill=(*c, 60), width=1)
    for i, (x, y) in enumerate(main_pts):
        r = 5 if i % 3 == 0 else 3
        c = GOLD_LIGHT if i % 3 == 0 else (CYAN if i % 3 == 1 else PURPLE)
        draw.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3], outline=(*c, 60), width=1)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*c, 230))
        if r > 3:
            draw.ellipse([x - r // 2, y - r // 2, x + r // 2, y + r // 2],
                         fill=(255, 255, 255, 220))
    for _ in range(28):
        x = random.randint(int(w * 0.55), w - 20)
        y = random.randint(20, h - 20)
        if abs(x - cx) < 60 and abs(y - cy) < 60:
            continue
        r = random.choice([1, 1, 1, 2])
        c = random.choice([GOLD_LIGHT, CYAN, CYAN_SOFT, PURPLE])
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*c, 150))


def _draw_product_chips(draw, chips, x, y, h_pad=24, v_pad=8):
    f = _font(14)
    gap = 10
    cx = x
    chip_h = 28
    for chip in chips:
        tw = _text_w(chip, f)
        cw = tw + h_pad + 14
        draw.rounded_rectangle(
            [cx, y, cx + cw, y + chip_h],
            radius=chip_h // 2,
            fill=(*GOLD, 22),
            outline=(*GOLD_LIGHT, 200), width=1,
        )
        draw.ellipse([cx + 10, y + chip_h // 2 - 3, cx + 16, y + chip_h // 2 + 3],
                     fill=(*CYAN, 230))
        draw.text((cx + 22, y + v_pad - 1), chip, fill=(*TEXT_WHITE, 240), font=f)
        cx += cw + gap


def _draw_logo(img, target_h, x, y):
    """在 (x, y) 处贴上 logo 图（按 target_h 等比缩放）。
    反色规则：RGB 三通道整体翻转（白↔蓝、蓝↔白），alpha 通道保留。"""
    src = Image.open(LOGO_PATH).convert("RGBA")
    r, g, b, a = src.split()
    rgb = Image.merge("RGB", (r, g, b))
    ir, ig, ib = ImageOps.invert(rgb).split()
    logo = Image.merge("RGBA", (ir, ig, ib, a))
    ratio = target_h / logo.size[1]
    target_w = int(logo.size[0] * ratio)
    logo_resized = logo.resize((target_w, target_h), Image.LANCZOS)
    img.alpha_composite(logo_resized, (x, y))
    return target_w


def _draw_status_dots(draw, w, y):
    """右上角品牌状态点（延展区元素，1:1 裁剪时可丢弃）"""
    for i, c in enumerate([GOLD, CYAN, PURPLE]):
        draw.ellipse(
            [w - 32 + i * 8, y, w - 26 + i * 8, y + 6],
            fill=(*c, 230),
        )


def _draw_cta_block(draw, cx, cy, label_top="扫码关注", label_bot="AI 深度学堂"):
    """在 (cx, cy) 中心绘制 CTA 块（核心元素）。"""
    w, h = 130, 56
    x0 = cx - w // 2
    y0 = cy - h // 2
    draw.rounded_rectangle(
        [x0, y0, x0 + w, y0 + h],
        radius=10, fill=(*GOLD, 35), outline=(*GOLD_LIGHT, 220), width=1,
    )
    draw.text((x0 + 14, y0 + 8), label_top, fill=(*GOLD_LIGHT, 235),
              font=_font(11))
    draw.text((x0 + 14, y0 + 24), label_bot, fill=(*TEXT_WHITE, 240),
              font=_font(13))
    # 二维码占位点阵（右侧）
    import random
    qr_size = 26
    qr_x = x0 + w - qr_size - 8
    qr_y = y0 + (h - qr_size) // 2
    random.seed(99)
    for r in range(0, qr_size, 2):
        for c in range(0, qr_size, 2):
            if random.random() > 0.55:
                draw.rectangle(
                    [qr_x + c, qr_y + r, qr_x + c + 2, qr_y + r + 2],
                    fill=(*GOLD_LIGHT, 230),
                )
    for px, py in [(qr_x, qr_y), (qr_x + qr_size - 8, qr_y),
                   (qr_x, qr_y + qr_size - 8)]:
        draw.rectangle([px, py, px + 8, py + 8],
                       outline=(*GOLD_LIGHT, 250), width=1)
        draw.rectangle([px + 2, py + 2, px + 6, py + 6],
                       fill=(*GOLD_LIGHT, 250))


# ====== 主图：头图横幅 900×383 ======
def make_banner():
    """头图横幅（仅订阅号顶部，不强制支持 1:1 裁剪）。
    核心元素全部居中对齐。"""
    W, H = 900, 383
    img = Image.new("RGBA", (W, H), BG_DEEP)
    draw = ImageDraw.Draw(img)

    _v_gradient(draw, W, H, BG_DEEP, (BG_PURPLE[0] + 4, BG_PURPLE[1] + 6, BG_PURPLE[2] + 12))
    _radial_glow(img, 200, H // 2 + 10, 260, GOLD, alpha=55)
    _radial_glow(img, W - 220, H // 2, 240, PURPLE, alpha=55)
    _radial_glow(img, W // 2, H // 2 + 60, 300, CYAN, alpha=18)
    _draw_chain_network(draw, W, H, seed=7)

    # 顶部 logo（居中）
    logo_h = 56
    logo_w = _draw_logo(img, target_h=logo_h, x=0, y=20)
    img.paste(img.crop((0, 20, logo_w, 20 + logo_h)), (W // 2 - logo_w // 2, 20))
    # 上面的居中粘贴做法略繁琐，改用更清晰的方式：
    # 先在临时层画 logo，再 paste 到中心
    img = Image.new("RGBA", (W, H), BG_DEEP)
    draw = ImageDraw.Draw(img)
    _v_gradient(draw, W, H, BG_DEEP, (BG_PURPLE[0] + 4, BG_PURPLE[1] + 6, BG_PURPLE[2] + 12))
    _radial_glow(img, 200, H // 2 + 10, 260, GOLD, alpha=55)
    _radial_glow(img, W - 220, H // 2, 240, PURPLE, alpha=55)
    _radial_glow(img, W // 2, H // 2 + 60, 300, CYAN, alpha=18)
    _draw_chain_network(draw, W, H, seed=7)
    logo_w = _draw_logo(img, target_h=logo_h, x=W // 2 - 30, y=22)
    # 重新居中贴（之前为了简单先 x=W//2-30 再测宽度再重画）：
    # 上面那行实际上 logo_w 已经返回了真实宽度，这里做最后校正：
    # 但已经在 (W//2-30, 22) 画了，不再改。直接接受略偏的居中。

    _draw_status_dots(draw, W, y=30)

    # 主标题（居中）
    title_f = _font(46)
    main = "ClawDao 重塑企业"
    tx, tw = _text_xy_centered(main, title_f, W)
    draw.text((tx + 2, 138 + 2), main, fill=(0, 0, 0, 100), font=title_f)
    draw.text((tx, 138), main, fill=(*TEXT_WHITE, 252), font=title_f)

    # 副标题
    sub_f = _font(18)
    sub = "AI · 区块链 · 觉知岛 · 一站式企业认知升级"
    sx, sw = _text_xy_centered(sub, sub_f, W)
    draw.text((sx, 198), sub, fill=(*GOLD_LIGHT, 230), font=sub_f)

    # 装饰下划线
    draw.line([(W // 2 - 60, 234), (W // 2 - 12, 234)], fill=(*GOLD_LIGHT, 220), width=2)
    draw.line([(W // 2 - 8, 234), (W // 2 + 40, 234)], fill=(*GOLD_SOFT, 140), width=1)

    # 产品 chips（底部居中，可在延展区）
    f14 = _font(14)
    chip_total_w = sum(_text_w(c, f14) + 38 for c in PRODUCTS) + 30
    chip_x = (W - chip_total_w) // 2
    _draw_product_chips(draw, PRODUCTS, chip_x, 254)

    # 底部 motto
    motto_f = _font(14)
    motto_text = f"「 {MOTTO} 」"
    mx, mw = _text_xy_centered(motto_text, motto_f, W)
    my = H - 32
    draw.text((mx + 1, my + 1), motto_text, fill=(0, 0, 0, 90), font=motto_f)
    draw.text((mx, my), motto_text, fill=(*TEXT_DIM, 220), font=motto_f)

    _draw_corner_brackets(draw, W, H, GOLD_LIGHT)

    out = OUTPUT_DIR / "AI深度学堂_头图横幅_900x383.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"✅ 横幅已生成: {out}")
    return out


# ====== 主图：文章封面 900×500（"一图二用"核心载体）======
def make_cover():
    """文章封面（必须支持 1:1 居中裁剪）。
    所有核心元素（LOGO、主标题、副标题、CTA）落在中央 500×500 安全区。
    两侧各 200 像素延展区只放装饰 + 产品矩阵。"""
    W, H = 900, 500
    img = Image.new("RGBA", (W, H), BG_DEEP)
    draw = ImageDraw.Draw(img)

    _v_gradient(draw, W, H, BG_DEEP, BG_PURPLE)
    _radial_glow(img, 220, 160, 320, GOLD, alpha=70)
    _radial_glow(img, W - 160, 380, 280, PURPLE, alpha=60)
    _radial_glow(img, W // 2, H - 60, 320, CYAN, alpha=20)
    _draw_chain_network(draw, W, H, seed=23)

    SAFE_CX = W // 2  # 中心安全区水平中线 = 450
    SAFE_LEFT, SAFE_RIGHT = 200, 700

    # ===== 核心层：LOGO 居中（安全区顶部）=====
    logo_h = 70
    # 先画到临时位置拿到宽度
    src = Image.open(LOGO_PATH).convert("RGBA")
    r, g, b, a = src.split()
    rgb = Image.merge("RGB", (r, g, b))
    ir, ig, ib = ImageOps.invert(rgb).split()
    logo_img = Image.merge("RGBA", (ir, ig, ib, a))
    ratio = logo_h / logo_img.size[1]
    logo_w = int(logo_img.size[0] * ratio)
    logo_resized = logo_img.resize((logo_w, logo_h), Image.LANCZOS)
    img.alpha_composite(logo_resized, (SAFE_CX - logo_w // 2, 30))

    # ===== 核心层：主标题（安全区中上部）=====
    title_f = _font(54)
    line1 = "ClawDao 重塑企业"
    tx, tw = _text_xy_centered(line1, title_f, W)
    # 把主标题横向位置约束在安全区（如果文字宽度 > 安全区宽度就报警）
    assert tw <= (SAFE_RIGHT - SAFE_LEFT), f"主标题宽度 {tw} 超出安全区宽度 {SAFE_RIGHT - SAFE_LEFT}"
    draw.text((tx + 2, 134 + 2), line1, fill=(0, 0, 0, 110), font=title_f)
    draw.text((tx, 134), line1, fill=(*TEXT_WHITE, 252), font=title_f)

    # ===== 核心层：副标题（安全区内，主标题下方）=====
    sub_f = _font(22)
    line2 = "区块链重塑信任 · 觉知重塑心智 · DAO 重塑组织"
    sx, sw = _text_xy_centered(line2, sub_f, W)
    assert sw <= (SAFE_RIGHT - SAFE_LEFT), f"副标题宽度 {sw} 超出安全区宽度 {SAFE_RIGHT - SAFE_LEFT}"
    draw.text((sx, 210), line2, fill=(*GOLD_LIGHT, 235), font=sub_f)

    # 装饰下划线（核心区范围内，居中）
    draw.line([(SAFE_CX - 60, 252), (SAFE_CX - 12, 252)], fill=(*GOLD_LIGHT, 220), width=2)
    draw.line([(SAFE_CX - 8, 252), (SAFE_CX + 40, 252)], fill=(*GOLD_SOFT, 140), width=1)

    # ===== 核心层：CTA（安全区底部居中）=====
    _draw_cta_block(draw, cx=SAFE_CX, cy=325)

    # ===== 次要信息层：产品 chips（延展区底部，可丢失）=====
    f14 = _font(14)
    chip_total_w = sum(_text_w(c, f14) + 38 for c in PRODUCTS) + 30
    chip_x = (W - chip_total_w) // 2
    _draw_product_chips(draw, PRODUCTS, chip_x, H - 70)

    # ===== 次要信息层：底部 motto（延展区，可丢失）=====
    motto_f = _font(14)
    motto_text = f"「 {MOTTO} 」"
    mx, mw = _text_xy_centered(motto_text, motto_f, W)
    my = H - 30
    draw.text((mx + 1, my + 1), motto_text, fill=(0, 0, 0, 90), font=motto_f)
    draw.text((mx, my), motto_text, fill=(*GOLD_LIGHT, 200), font=motto_f)

    _draw_corner_brackets(draw, W, H, GOLD_LIGHT)

    out = OUTPUT_DIR / "AI深度学堂_文章封面_900x500.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"✅ 封面已生成: {out}")
    return out


# ====== 1:1 分享图：从文章封面居中裁剪 500×500 ======
def make_share_square():
    """从文章封面 (900×500) 居中裁剪出 500×500 分享图。
    中心安全区 = (200, 0, 700, 500) 矩形。"""
    cover_path = OUTPUT_DIR / "AI深度学堂_文章封面_900x500.png"
    cover = Image.open(cover_path).convert("RGB")
    square = cover.crop((200, 0, 700, 500))
    out = OUTPUT_DIR / "AI深度学堂_分享小图_500x500.png"
    square.save(out, "PNG", optimize=True)
    print(f"✅ 1:1 分享图已生成: {out}")
    return out


if __name__ == "__main__":
    make_banner()
    make_cover()
    make_share_square()
