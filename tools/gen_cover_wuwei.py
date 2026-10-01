#!/usr/bin/env python3
"""
为「无为而治×AI：管人是上个时代的事，设计系统才是这个时代的事」生成封面。

设计要点：
- 900×500 文章封面 + 500×500 1:1 分享图（一图二用）
- 中心 500×500 安全区内：LOGO、主标题、副标题、CTA
- 黑金主题（深空蓝底 + 暖金辉光）
- 主标题：两行（不超过安全区 500px 宽）
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(2026)

OUTPUT_DIR = Path("/Users/imfly/projects/Agents/clawdao-wechat-agent/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ===== 调色板（黑金主题） =====
C = {
    "bg_top":      (4, 4, 12),       # 深空黑
    "bg_bottom":   (10, 8, 24),      # 深空蓝
    "bg_mid":      (8, 6, 18),
    "gold":        (200, 165, 55),   # 主金
    "gold_bright": (235, 200, 95),   # 高光金
    "gold_dim":    (140, 105, 35),   # 暗金
    "gold_glow":   (220, 180, 70),   # 辉光金
    "white":       (248, 245, 235),  # 文字白
    "text_dim":    (175, 170, 160),  # 副文字
}

FONT_REG = "/System/Library/Fonts/PingFang.ttc"
FONT_MED = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = FONT_MED if bold else FONT_LIGHT
    return ImageFont.truetype(path, size)


def draw_vertical_gradient(img: Image.Image, top: tuple, bottom: tuple):
    """从上到下垂直渐变"""
    w, h = img.size
    for y in range(h):
        ratio = y / max(1, h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        ImageDraw.Draw(img).line([(0, y), (w, y)], fill=(r, g, b))


def draw_radial_glow(img: Image.Image, center: tuple, radius: int, color: tuple, alpha: int = 110):
    """中心暖光晕"""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(radius, 0, -8):
        a = int(alpha * (1 - i / radius))
        od.ellipse(
            [center[0] - i, center[1] - i, center[0] + i, center[1] + i],
            outline=(*color, a),
            width=8,
        )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=40))
    img.alpha_composite(overlay)


def draw_grid(img: Image.Image, color: tuple, spacing: int = 36, alpha: int = 22):
    """极简网格背景（仅延展区装饰）"""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(0, w, spacing):
        od.line([(x, 0), (x, h)], fill=(*color, alpha), width=1)
    for y in range(0, h, spacing):
        od.line([(0, y), (w, y)], fill=(*color, alpha), width=1)
    img.alpha_composite(overlay)


def draw_particles(img: Image.Image, count: int = 60, color: tuple = C["gold"]):
    """金色粒子点缀（装饰层）"""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.choice([1, 1, 1, 2, 2, 3])
        a = random.randint(40, 140)
        od.ellipse([x - r, y - r, x + r, y + r], fill=(*color, a))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.5))
    img.alpha_composite(overlay)


def measure(draw: ImageDraw.ImageDraw, text: str, fnt) -> tuple:
    """中英文宽度测量"""
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_text(draw, text: str, fnt, max_width: int) -> ImageFont.FreeTypeFont:
    """文字过长时按比例缩小字号"""
    cur = fnt
    w, _ = measure(draw, text, cur)
    if w <= max_width:
        return cur
    # 等比例缩小
    ratio = max_width / w
    new_size = max(10, int(cur.size * ratio))
    return ImageFont.truetype(cur.path, new_size)


def render_article_cover() -> Path:
    """900×500 文章封面"""
    W, H = 900, 500
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    # 1) 背景渐变
    draw_vertical_gradient(img, C["bg_top"], C["bg_bottom"])

    # 2) 装饰层：极简网格 + 金粒子（全部延展区 200-700 之外）
    draw_grid(img, C["gold_dim"], spacing=40, alpha=18)
    draw_particles(img, count=80, color=C["gold_glow"])

    # 3) 中心辉光（落在 500×500 安全区内，作为主标题视觉锚点）
    draw_radial_glow(img, center=(450, 240), radius=320, color=C["gold"], alpha=85)

    # ============ 核心层（必须落在 200~700 横向安全区） ============

    # 4) 顶部品牌条（小标识，安全区内顶部）
    brand_font = font(20, bold=True)
    brand_text = "亿检链 · LIMSCHAIN"
    bw, bh = measure(draw, brand_text, brand_font)
    bx = (W - bw) // 2
    by = 70
    # 品牌左侧短装饰线
    draw.rectangle([bx - 30, by + bh // 2 - 1, bx - 12, by + bh // 2 + 1], fill=C["gold"])
    draw.rectangle([bx + bw + 12, by + bh // 2 - 1, bx + bw + 30, by + bh // 2 + 1], fill=C["gold"])
    draw.text((bx, by), brand_text, font=brand_font, fill=C["gold_bright"])

    # 5) 主标题（两行，控制在 500px 安全区内）
    title_font = font(40, bold=True)
    line1 = "无为而治 × AI"
    line2 = "管人是上个时代的事"

    # 自适应缩放
    title_font = fit_text(draw, line1, title_font, max_width=480)
    title_font = fit_text(draw, line2, title_font, max_width=480)

    l1w, l1h = measure(draw, line1, title_font)
    l2w, l2h = measure(draw, line2, title_font)

    # 主标题在垂直中部偏上
    block_top = 150
    gap = 16
    l1x = (W - l1w) // 2
    l2x = (W - l2w) // 2
    l1y = block_top
    l2y = l1y + l1h + gap
    draw.text((l1x, l1y), line1, font=title_font, fill=C["white"])
    draw.text((l2x, l2y), line2, font=title_font, fill=C["white"])

    # 6) 副标题（呼应本文核心钩子）
    sub_font = font(20, bold=False)
    sub_text = "设计系统，才是这个时代的事"
    sub_font = fit_text(draw, sub_text, sub_font, max_width=460)
    sw, sh = measure(draw, sub_text, sub_font)
    sub_y = l2y + l2h + 22
    draw.text(((W - sw) // 2, sub_y), sub_text, font=sub_font, fill=C["gold_bright"])

    # 7) CTA 引导（金色短横 + 关键词，落在安全区底部）
    cta_font = font(15, bold=True)
    cta_text = "可检测 · 可决策 · 可执行 · 可追溯"
    cw, ch = measure(draw, cta_text, cta_font)
    cy = 420
    cx = (W - cw) // 2
    # CTA 上下两条细线
    draw.rectangle([cx - 8, cy + ch // 2 - 1, cx - 2, cy + ch // 2 + 1], fill=C["gold"])
    draw.rectangle([cx + cw + 2, cy + ch // 2 - 1, cx + cw + 8, cy + ch // 2 + 1], fill=C["gold"])
    draw.text((cx, cy), cta_text, font=cta_font, fill=C["gold"])

    # ============ 次要层（可落在延展区） ============
    # 左下角作者署名（次要层）
    author_font = font(13, bold=False)
    draw.text((50, H - 40), "顺道大叔  ·  亿检链主理人", font=author_font, fill=C["text_dim"])

    # 右下角日期（次要层）
    date_font = font(13, bold=False)
    date_text = "LIMSCHAIN · 2026"
    dw, dh = measure(draw, date_text, date_font)
    draw.text((W - dw - 50, H - 40), date_text, font=date_font, fill=C["text_dim"])

    # 8) 整体锐化
    img = img.convert("RGB")

    out_path = OUTPUT_DIR / "亿检链_文章封面_900x500.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"✅ 已生成文章封面: {out_path}  ({img.size})")
    return out_path


def render_square_share() -> Path:
    """500×500 1:1 分享图（从文章封面中心 500×500 裁剪区域单独渲染）"""
    # 直接复用文章封面，居中裁剪 200~700 区域
    cover = Image.open(OUTPUT_DIR / "亿检链_文章封面_900x500.png")
    square = cover.crop((200, 0, 700, 500))
    out_path = OUTPUT_DIR / "亿检链_分享小图_500x500.png"
    square.save(out_path, "PNG", optimize=True)
    print(f"✅ 已生成 1:1 分享图: {out_path}  ({square.size})")
    return out_path


if __name__ == "__main__":
    render_article_cover()
    render_square_share()
