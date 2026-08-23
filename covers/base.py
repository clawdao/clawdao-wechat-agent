import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pathlib import Path
import sys
sys.path.insert(0, '/Users/imfly/Documents/公众号')
from config import get_cover_config, get_output_dir

# ===== 觉知岛 品牌配色方案 =====
BRAND_THEMES = [
    # 玄墨金 - 深邃智慧（旗舰版）
    {"bg": (2, 4, 10), "accent": (220, 185, 60), "accent_soft": (140, 115, 50),
     "text": (255, 255, 255), "text_dim": (170, 165, 160),
     "glow": (255, 215, 0, 22), "aura": (212, 175, 55, 8)},
    # 烟霞紫金 - 禅意空灵
    {"bg": (12, 6, 20), "accent": (215, 185, 70), "accent_soft": (120, 95, 55),
     "text": (255, 255, 255), "text_dim": (175, 160, 165),
     "glow": (225, 195, 85, 18), "aura": (180, 140, 60, 7)},
    # 渊蓝鎏金 - 沉稳力量
    {"bg": (2, 6, 16), "accent": (205, 175, 65), "accent_soft": (110, 95, 55),
     "text": (255, 255, 255), "text_dim": (160, 165, 175),
     "glow": (215, 190, 75, 18), "aura": (160, 140, 60, 7)},
    # 檀褐赤金 - 温润厚重
    {"bg": (10, 6, 6), "accent": (222, 170, 55), "accent_soft": (115, 85, 42),
     "text": (255, 255, 255), "text_dim": (170, 160, 150),
     "glow": (235, 185, 65, 18), "aura": (180, 130, 50, 7)},
]

BRAND_NAME = "觉知岛"
TAGLINE = "AI · 区块链 · 认知升级"
MOTTO = "知人者智，自知者明"
VALUES = "明道 · 取势 · 优术 · 利他"

def _font(size):
    paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def _gradient(draw, w, h, c1, c2):
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def _draw_mountains(draw, w, h, accent):
    """底部远山"""
    pts = [(0, h), (0, h-28), (60, h-48), (120, h-33), (180, h-52),
            (240, h-38), (300, h-52), (360, h-42), (420, h-55),
            (480, h-42), (540, h-52), (600, h-55), (660, h-42),
            (720, h-52), (780, h-38), (840, h-48), (w, h-33), (w, h)]
    draw.polygon(pts, fill=(*accent, 5))

def _draw_stars(draw, w, h, accent, seed):
    np.random.seed(abs(seed) & 0xFFFFFFFF)
    for _ in range(35):
        x = np.random.randint(15, w-15)
        y = np.random.randint(15, h-55)
        r = np.random.choice([0.5, 0.5, 1, 1, 1.5])
        alpha = np.random.randint(6, 22)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*accent, alpha))

def _draw_human(draw, w, h, accent):
    """右侧禅坐人物 - 更清晰的主体轮廓"""
    cx = w - 105
    by = h - 62
    ac_dark = (accent[0]//2, accent[1]//2, accent[2]//2)
    
    # 底部莲座光晕
    for r in range(30, 0, -3):
        a = max(4, 18 - r)
        draw.ellipse([cx-r, by-4-r//2, cx+r, by-4+r//2], fill=(*accent, a))
    
    head_y = by - 130
    
    # 头部光晕
    for r in range(22, 0, -2):
        a = max(12, 40 - r)
        draw.ellipse([cx-r, head_y-r, cx+r, head_y+r], fill=(*accent, a))
    
    # 头部实心
    draw.ellipse([cx-12, head_y-12, cx+12, head_y+12], fill=ac_dark)
    
    # 头顶灵光
    draw.ellipse([cx-2.5, head_y-17, cx+2.5, head_y-12], fill=(*accent, 230))
    for deg in range(-15, 16, 8):
        rad = math.radians(deg)
        draw.line([(cx, head_y-13), (cx+math.sin(rad)*28, head_y-20+abs(math.cos(rad))*16)],
                  fill=(*accent, 22), width=1)
    
    # 身体 - 流畅坐姿
    body = [
        (cx, by-112), (cx-22, by-90), (cx-24, by-78),
        (cx-10, by-70), (cx+10, by-70), (cx+24, by-78),
        (cx+22, by-90), (cx, by-112)
    ]
    draw.polygon([(x,y) for x,y in body], fill=(*ac_dark, 70))
    for i in range(len(body)-1):
        draw.line([body[i], body[i+1]], fill=(*accent, 45), width=2)
    draw.line([body[-1], body[0]], fill=(*accent, 45), width=2)
    
    # 盘腿
    for dx in [-10, 10]:
        draw.ellipse([cx+dx-7, by-45-3, cx+dx+7, by-45+3], fill=ac_dark)
    
    # 合十金光
    draw.ellipse([cx-2.5, by-74, cx+2.5, by-69], fill=(*accent, 120))

def _draw_geometric(draw, w, h, accent):
    """左上几何装饰"""
    cx, cy = 70, h//2-15
    for r in range(30, 80, 5):
        a = max(2, 9 - (r-30)//10)
        draw.ellipse([cx-r, cy-r//2, cx+r, cy+r//2], outline=(*accent, a), width=1)
    draw.ellipse([cx-1.5, cy-1.5, cx+1.5, cy+1.5], fill=(*accent, 55))

def _draw_halo_ring(draw, w, h, accent):
    draw.ellipse([55, h//2-35, 105, h//2+15], outline=(*accent, 8), width=1)

def _draw_vline(draw, w, h, accent):
    x = 18
    draw.line([(x, 35), (x, h-35)], fill=(*accent, 10), width=1)
    for dy in [0, 5, 10]:
        draw.line([(x-2, h-35-dy), (x+2, h-35-dy)], fill=(*accent, 14-dy), width=1)

def _draw_right_nodes(draw, w, h, accent):
    pts = [(w-210, 55), (w-170, 25), (w-150, 65), (w-190, 95), (w-130, 85)]
    for px, py in pts:
        draw.ellipse([px-1.2, py-1.2, px+1.2, py+1.2], fill=(*accent, 25))
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            draw.line([pts[i], pts[j]], fill=(*accent, 5), width=1)

def generate_cover(title, topic=""):
    cfg = get_cover_config()
    out_dir = get_output_dir()
    W, H = cfg["width"], cfg["height"]

    # 根据文章主题选择配色方案（内容匹配）
    seed_str = (title or "") + (topic or "")
    idx = hash(seed_str) % len(BRAND_THEMES)
    theme = BRAND_THEMES[idx]

    img = Image.new("RGBA", (W, H), theme["bg"])
    draw = ImageDraw.Draw(img)

    _gradient(draw, W, H, theme["bg"], (theme["bg"][0]+4, theme["bg"][1]+5, theme["bg"][2]+7))
    _draw_mountains(draw, W, H, theme["accent"])
    _draw_stars(draw, W, H, theme["accent"], hash(title))
    _draw_halo_ring(draw, W, H, theme["accent"])
    _draw_geometric(draw, W, H, theme["accent"])
    _draw_vline(draw, W, H, theme["accent"])
    _draw_right_nodes(draw, W, H, theme["accent"])
    _draw_human(draw, W, H, theme["accent"])

        # === 文字（1:1安全区居中布局）===
    SAFE_LEFT, SAFE_RIGHT = 200, 700
    SAFE_CX = (SAFE_LEFT + SAFE_RIGHT) // 2

    # 1. 品牌名（安全区内居中）
    brand_text = f"◆ {BRAND_NAME}"
    bb_brand = _font(16).getbbox(brand_text)
    brand_w = bb_brand[2] - bb_brand[0]
    bx = SAFE_CX - brand_w // 2
    draw.text((bx, 20), brand_text, fill=(*theme["accent"], 240), font=_font(16))
    draw.line([(SAFE_CX - 22, 42), (SAFE_CX + 22, 42)], fill=(*theme["accent"], 130), width=1)
    draw.line([(SAFE_CX - 16, 45), (SAFE_CX + 16, 45)], fill=(*theme["accent"], 60), width=1)

    # 2. 标题（安全区内居中，最多2行）
    safe_w = SAFE_RIGHT - SAFE_LEFT - 40
    f_t1 = _font(40)
    lines, cur = [], ""
    for ch in title:
        test = cur + ch
        bb = f_t1.getbbox(test)
        if bb and bb[2] > safe_w:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur: lines.append(cur)
    if not lines: lines = ["好文"]
    if len(lines) > 2:
        f_t1 = _font(30)
        lines = lines[:2]
        if len(lines[1]) > 18:
            lines[1] = lines[1][:17] + "…"

    lh = f_t1.getbbox("测")[3] + 10
    th = len(lines) * lh + 8
    sy = (H - th) // 2 - 15

    for i, line in enumerate(lines):
        y = sy + i * lh
        bb_line = f_t1.getbbox(line)
        line_w = bb_line[2] - bb_line[0]
        lx = SAFE_CX - line_w // 2
        draw.text((lx + 1, y + 1), line, fill=(0, 0, 0, 70), font=f_t1)
        draw.text((lx, y), line, fill=(*theme["text"], 250), font=f_t1)

    # 3. 道德经（安全区内，标题下方居中）
    motto_text = f"「 {MOTTO} 」"
    bb_motto = _font(14).getbbox(motto_text)
    motto_w = bb_motto[2] - bb_motto[0]
    mx = SAFE_CX - motto_w // 2
    my = sy + th + 28
    draw.text((mx, my), motto_text, fill=(*theme["accent"], 215), font=_font(14))

    # 4. 分隔线（安全区内居中）
    sep_y = my + 26
    draw.line([(SAFE_CX - 22, sep_y), (SAFE_CX + 22, sep_y)], fill=(*theme["accent"], 140), width=1)
    draw.line([(SAFE_CX - 16, sep_y + 3), (SAFE_CX + 16, sep_y + 3)], fill=(*theme["accent"], 60), width=1)

    # 5. 价值观（安全区内居中）
    bb_vals = _font(13).getbbox(VALUES)
    vals_w = bb_vals[2] - bb_vals[0]
    vx = SAFE_CX - vals_w // 2
    draw.text((vx, sep_y + 12), VALUES, fill=(*theme["accent"], 175), font=_font(13))

    # 6. 底部tag（安全区内居中）
    bb_tag = _font(13).getbbox(TAGLINE)
    tag_w = bb_tag[2] - bb_tag[0]
    tx = SAFE_CX - tag_w // 2
    draw.text((tx, H - 28), TAGLINE, fill=(*theme["text_dim"], 190), font=_font(13))

    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:20])
    path = out_dir / f"cover_{safe}.png"
    img.convert("RGB").save(path, "PNG", optimize=True)
    print(f"✅ 封面图已生成: {path}")
    return path

if __name__ == "__main__":
    generate_cover("AI时代老板如何提升认知", "认知升级")
    generate_cover("区块链如何重塑未来商业", "区块链")
