#!/usr/bin/env python3
"""
「SaaS 越买越焦虑？少则得，多则惑」
专属封面 & 插图 — 超高精度设计引擎（4x超采样）
================================================
设计概念：「由繁入简」
- 左侧 SaaS 碎片混乱 → 右侧归一清明
- 深墨蓝渐变底 × 暖金辉光 = 清醒、克制、高级
- 4x 超采样 + 多层渐变 + 辉光文字 + 粒子系统

输出：
  - output/觉知岛_文章封面_900x500.png
  - output/觉知岛_头图横幅_900x383.png
  - output/觉知岛_分享小图_500x500.png
  - output/inline_三大陷阱_concept.png
  - output/inline_三步法_steps.png
  - output/inline_金句_quote.png
"""

import math, os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

random.seed(42)

# ===== 超采样倍率 =====
SCALE = 4

# ===== 输出目录 =====
OUTPUT_DIR = Path("/Users/imfly/Documents/projects/Codex-Agents-运营/公众号工厂/output")

# ===== 品牌常量 =====
BRAND = "觉知岛"
MOTTO = "知人者智，自知者明"

# ===== 配色方案：「由繁入简」专属 =====
# 墨蓝 × 暖金 × 纯粹白
C = {
    "bg_top":       (2, 8, 22),      # 深墨蓝
    "bg_bottom":    (8, 16, 35),     # 深蓝底
    "bg_mid":       (5, 12, 28),     # 中间
    "gold":         (212, 175, 55),  # 主金色
    "gold_bright":  (245, 215, 85),  # 高亮金
    "gold_dim":     (155, 125, 38),  # 暗金
    "gold_glow":    (230, 195, 65),  # 辉光金
    "amber":        (195, 135, 25),  # 琥珀
    "white":        (255, 255, 248), # 主文字白
    "text_dim":     (185, 180, 175), # 副文字
    "scatter_chaos":(190, 155, 60, 20), # 散乱粒子
    "scatter_order":(212, 175, 55, 12), # 有序粒子
    "accent_blue":  (50, 70, 150, 35),  # 蓝紫光
}

FONT_DIR = Path("/System/Library/Fonts")

def _font(size, bold=False):
    name = "PingFang.ttc"
    path = FONT_DIR / name
    if path.exists():
        try:
            return ImageFont.truetype(str(path), int(size * SCALE))
        except:
            pass
    return ImageFont.load_default()

# ===== 核心绘制工具 =====

def _linear_gradient_v(draw, w, h, c1, c2):
    """垂直线性渐变：上→下"""
    for y in range(h * SCALE):
        ratio = y / (h * SCALE)
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.line([(0, y), (w * SCALE, y)], fill=(r, g, b))

def _linear_gradient_h(draw, w, h, c1, c2):
    """水平线性渐变：左→右"""
    for x in range(w * SCALE):
        ratio = x / (w * SCALE)
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.line([(x, 0), (x, h * SCALE)], fill=(r, g, b))

def _radial_glow(draw, cx, cy, radius, color, alpha=60):
    """径向辉光圆"""
    max_r = radius * SCALE
    cx_s, cy_s = cx * SCALE, cy * SCALE
    for r in range(int(max_r), 0, -2):
        ratio = r / max_r
        a = int(alpha * (1 - ratio))
        if a < 1:
            continue
        draw.ellipse([(cx_s - r, cy_s - r), (cx_s + r, cy_s + r)],
                      fill=(*color[:3], a))

def _draw_text_with_glow(draw, x, y, text, font, color, glow_color=None, alpha=80):
    """绘制带辉光的文字"""
    s = SCALE
    if glow_color:
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x * s + dx * s, y * s + dy * s), text,
                          fill=(*glow_color[:3], alpha), font=font)
    draw.text((x * s, y * s), text, fill=color, font=font)

def _draw_particles_dense(draw, w, h, count=80):
    """绘制密集散乱粒子（左侧=SaaS混乱）"""
    p = C["scatter_chaos"]
    s = SCALE
    for _ in range(count):
        x = random.randint(15, int(w * 0.45))
        y = random.randint(5, h - 5)
        r = random.choice([0.6, 1.0, 1.4, 1.8, 2.2, 2.8]) * s
        a = random.randint(3, 18)
        draw.ellipse([(x * s - r, y * s - r), (x * s + r, y * s + r)],
                      fill=(*p[:3], a))

def _draw_particles_sparse(draw, w, h, count=25):
    """绘制稀疏有序粒子（右侧=归一清明）"""
    p = C["scatter_order"]
    s = SCALE
    for _ in range(count):
        x = random.randint(int(w * 0.55), w - 15)
        y = random.randint(10, h - 10)
        r = random.choice([0.8, 1.2, 1.6]) * s
        a = random.randint(5, 15)
        draw.ellipse([(x * s - r, y * s - r), (x * s + r, y * s + r)],
                      fill=(*p[:3], a))

def _draw_chaos_lines(draw, w, h):
    """绘制左侧混乱线条（SaaS碎片化）"""
    p = C["gold_dim"]
    s = SCALE
    for _ in range(12):
        x1 = random.randint(10, int(w * 0.4))
        y1 = random.randint(10, h - 10)
        x2 = x1 + random.randint(15, 50)
        y2 = y1 + random.randint(-20, 20)
        a = random.randint(8, 25)
        draw.line([(x1 * s, y1 * s), (x2 * s, y2 * s)],
                  fill=(*p, a), width=random.choice([1, 2]) * s)

def _draw_converge_paths(draw, w, h, cx_target, cy_target):
    """绘制从左侧汇聚到中心的光迹"""
    s = SCALE
    p = C["gold"]
    for _ in range(16):
        sy = random.randint(30, h - 30)
        sx = random.randint(20, int(w * 0.35))
        steps = 25
        prev_x, prev_y = None, None
        for t in range(steps + 1):
            ratio = t / steps
            # 贝塞尔曲线
            ctrl_x = (sx + (cx_target - sx) * 0.3 + random.randint(-25, 25))
            ctrl_y = (sy + (cy_target - sy) * 0.15 + random.randint(-15, 15))
            bx = int((1 - ratio)**2 * sx + 2 * (1 - ratio) * ratio * ctrl_x + ratio**2 * cx_target)
            by = int((1 - ratio)**2 * sy + 2 * (1 - ratio) * ratio * ctrl_y + ratio**2 * cy_target)
            a = int(15 * (1 - ratio) * (1 - ratio))
            if a < 1:
                break
            if prev_x is not None:
                draw.line([(prev_x, prev_y), (bx * s, by * s)],
                          fill=(*p, a), width=max(1, int(1.2 * s * (1 - ratio))))
            prev_x, prev_y = bx * s, by * s

def _draw_unity_mandala(draw, cx, cy, r):
    """绘制代表「归一」的曼陀罗圆环"""
    s = SCALE
    colors = [C["gold_dim"], C["gold"], C["gold_bright"]]
    
    # 最外圈辉光
    _radial_glow(draw, cx, cy, r + 30, C["gold_glow"], 25)
    
    # 同心圆环
    for i, mult in enumerate([1.0, 0.82, 0.64, 0.46, 0.28, 0.12]):
        rr = int(r * mult * s)
        if rr < 2:
            continue
        col = colors[i % 3]
        alpha = int(55 + 40 * (1 - abs(mult - 0.5) * 2))
        w_mult = int(max(1, (1.5 + 0.8 * (1 - mult)) * s))
        draw.ellipse([(cx * s - rr, cy * s - rr),
                       (cx * s + rr, cy * s + rr)],
                      outline=(*col, alpha), width=w_mult)
    
    # 中心闪耀
    _radial_glow(draw, cx, cy, int(r * 0.15), C["gold_bright"], 70)
    _radial_glow(draw, cx, cy, int(r * 0.08), (255, 255, 255), 50)
    
    # 射线（从中心向外辐射）
    for angle_deg in range(0, 360, 20):
        rad = math.radians(angle_deg)
        x1 = cx + math.cos(rad) * r * 0.12
        y1 = cy + math.sin(rad) * r * 0.12
        x2 = cx + math.cos(rad) * r * 0.92
        y2 = cy + math.sin(rad) * r * 0.92
        a = random.randint(10, 25)
        draw.line([(x1 * s, y1 * s), (x2 * s, y2 * s)],
                  fill=(*C["gold"], a), width=max(1, int(1.0 * s)))

# ===== 核心封面生成 =====

def generate_cover_set():
    """生成封面三件套"""
    sizes = {
        "cover":   (900, 500),
        "banner":  (900, 383),
        "square":  (500, 500),
    }
    
    W, H = sizes["cover"]
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    # 1. 垂直渐变背景
    _linear_gradient_v(draw, W, H, C["bg_top"], C["bg_bottom"])
    
    # 2. 水平渐变叠加（左深右亮）
    _linear_gradient_h(draw, W, H,
                       (C["bg_top"][0], C["bg_top"][1], C["bg_top"][2], 0),
                       (C["bg_bottom"][0] + 15, C["bg_bottom"][1] + 10, C["bg_bottom"][2] + 30, 0))
    
    # 3. 背景大光晕（右半部）
    _radial_glow(draw, int(W * 0.72), int(H * 0.5), 220, C["accent_blue"], 30)
    _radial_glow(draw, int(W * 0.68), int(H * 0.45), 160, C["gold_glow"], 18)
    
    # 4. 左侧密集散乱粒子（SaaS 碎片化焦虑）
    _draw_particles_dense(draw, W, H, count=70)
    _draw_chaos_lines(draw, W, H)
    
    # 5. 汇聚光迹（从左→中心）
    _draw_converge_paths(draw, W, H, int(W * 0.65), int(H * 0.48))
    
    # 6. 右侧有序粒子（归一后的清明）
    _draw_particles_sparse(draw, W, H, count=20)
    
    # 7. 中心归一曼陀罗圆环
    _draw_unity_mandala(draw, int(W * 0.70), int(H * 0.48), int(min(W, H) * 0.14))
    
    # 8. 标题文字（安全区内）
    safe_center_x = W // 2
    
    ft_title = _font(24, bold=True)
    ft_sub = _font(15, bold=False)
    ft_motto = _font(10)
    
    title_pos_y = int(H * 0.12)
    
    # 主标题行1: SaaS 越买越焦虑？
    _draw_text_with_glow(draw, safe_center_x - 170, title_pos_y, "SaaS 越买越焦虑？",
                         ft_title, C["gold_bright"], C["gold_glow"], 60)
    
    # 主标题行2: 少则得，多则惑
    ft_title2 = _font(28, bold=True)
    _draw_text_with_glow(draw, safe_center_x - 140, title_pos_y + 60, "少则得，多则惑",
                         ft_title2, C["white"], C["gold_glow"], 50)
    
    # 副标题
    _draw_text_with_glow(draw, safe_center_x - 120, title_pos_y + 130,
                         "一个系统，顶一屋子 SaaS",
                         ft_sub, C["gold_dim"], C["gold"], 20)
    
    # 品牌 motto
    _draw_text_with_glow(draw, safe_center_x - 60, int(H * 0.85),
                         f"「{MOTTO}」",
                         ft_motto, C["text_dim"], None, 0)
    
    # 品牌名
    _draw_text_with_glow(draw, safe_center_x - 25, int(H * 0.92),
                         f"—— {BRAND}",
                         ft_motto, C["gold_dim"], None, 0)
    
    # 9. 左下装饰线
    draw.line([(10 * s, int(H * 0.85) * s), (10 * s, int(H * 0.95) * s)],
              fill=(*C["gold"], 35), width=2 * s)
    draw.line([(10 * s, int(H * 0.90) * s), (30 * s, int(H * 0.90) * s)],
              fill=(*C["gold"], 35), width=2 * s)
    
    # 10. 右下装饰线
    draw.line([((W - 10) * s, int(H * 0.85) * s), ((W - 10) * s, int(H * 0.95) * s)],
              fill=(*C["gold"], 20), width=2 * s)
    draw.line([((W - 10) * s, int(H * 0.90) * s), ((W - 30) * s, int(H * 0.90) * s)],
              fill=(*C["gold"], 20), width=2 * s)
    
    # ── 缩放为最终尺寸 ──
    def _resize(img, size):
        return img.resize(size, Image.LANCZOS)
    
    # ── 保存文章封面 ──
    cover_final = _resize(img, sizes["cover"])
    cover_path = OUTPUT_DIR / "觉知岛_文章封面_900x500.png"
    cover_final.convert("RGB").save(str(cover_path), "PNG", optimize=True)
    print(f"✅ 文章封面: {cover_path} ({cover_path.stat().st_size // 1024}KB)")
    
    # ── 头图横幅 900×383 ──
    banner_h = 383
    crop_top = (H - banner_h) // 2
    banner_img = img.crop((0, crop_top * s, W * s, (crop_top + banner_h) * s))
    banner_final = _resize(banner_img, (900, 383))
    banner_path = OUTPUT_DIR / "觉知岛_头图横幅_900x383.png"
    banner_final.convert("RGB").save(str(banner_path), "PNG", optimize=True)
    print(f"✅ 头图横幅: {banner_path} ({banner_path.stat().st_size // 1024}KB)")
    
    # ── 分享小图 500×500 ──
    square = img.crop((200 * s, 0, 700 * s, 500 * s))
    square_final = _resize(square, (500, 500))
    square_path = OUTPUT_DIR / "觉知岛_分享小图_500x500.png"
    square_final.convert("RGB").save(str(square_path), "PNG", optimize=True)
    print(f"✅ 分享小图: {square_path} ({square_path.stat().st_size // 1024}KB)")
    
    return cover_path, banner_path, square_path


# ===== 内嵌插图生成 =====

def generate_inline_concept():
    """
    概念插图：SaaS 租约陷阱
    尺寸：640×400
    设计：展示SaaS月租堆积，视觉化"租约"概念
    """
    W, H = 640, 400
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    _linear_gradient_v(draw, W, H, C["bg_top"], C["bg_mid"])
    _radial_glow(draw, W // 2, H // 2, 200, C["accent_blue"], 20)
    
    # 概念元素：三叠SaaS账单/租约
    items = [
        ("📋", "SaaS 月租", "年涨 20%-40%"),
        ("🔗", "数据锁定", "迁移成本高"),
        ("📈", "被动涨价", "无议价权"),
    ]
    
    spacing = (W - 60) // 3
    start_x = 30
    
    for idx, (icon, title_text, desc) in enumerate(items):
        cx = start_x + spacing * idx + spacing // 2
        
        # 矩形卡片
        box_w, box_h = spacing - 20, 230
        box_x = cx - box_w // 2
        box_y = 90
        
        draw.rounded_rectangle(
            [(box_x * s, box_y * s), ((box_x + box_w) * s, (box_y + box_h) * s)],
            radius=12 * s,
            fill=(*C["bg_mid"], 180),
            outline=(*C["gold_dim"], 35),
            width=1 * s
        )
        
        _radial_glow(draw, cx, box_y + 40, 50, C["gold_glow"], 12)
        
        # Icon
        ft_icon = _font(30)
        draw.text((cx * s - 15 * s, (box_y + 15) * s), icon,
                  fill=(*C["gold_bright"], 200), font=ft_icon)
        
        # Title
        ft_t = _font(13, bold=True)
        draw.text((cx * s - 45 * s, (box_y + 75) * s), title_text,
                  fill=(*C["gold_bright"], 230), font=ft_t)
        
        # Desc
        ft_d = _font(10)
        draw.text((cx * s - 50 * s, (box_y + 120) * s), desc,
                  fill=(*C["text_dim"], 180), font=ft_d)
    
    # 顶部标题
    ft_header = _font(16, bold=True)
    draw.text((W // 2 * s - 110 * s, 18 * s), "⚠  你买的不是软件，是一叠租约",
              fill=(*C["gold_bright"], 200), font=ft_header)
    
    final = img.resize((W, H), Image.LANCZOS)
    path = OUTPUT_DIR / "inline_三大陷阱_concept.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 概念插图: {path} ({path.stat().st_size // 1024}KB)")
    return path


def generate_inline_steps():
    """
    步骤插图：三步减少依赖
    尺寸：640×400
    """
    W, H = 640, 400
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    _linear_gradient_v(draw, W, H, C["bg_top"], C["bg_mid"])
    _radial_glow(draw, W // 2, H // 2, 180, C["gold_glow"], 12)
    
    steps = [
        ("①", "盘点清单", "列出每月SaaS支出\n知道在依赖什么"),
        ("②", "选突破口", "挑最痛的场景\n从最小闭环开始"),
        ("③", "建自长系统", "统一平台替代碎SaaS\n越用越强"),
    ]
    
    spacing = (W - 80) // 3
    start_x = 40
    
    for idx, (num, step_title, step_desc) in enumerate(steps):
        cx = start_x + spacing * idx + spacing // 2
        cy = H // 2 - 5
        
        circle_r = 58
        
        # 背景辉光
        for r in range(int(circle_r * s) + 10, 0, -6):
            ratio = r / ((circle_r + 10) * s)
            a = int(15 * (1 - ratio) * ratio)
            if a < 2:
                continue
            draw.ellipse([(cx * s - r, cy * s - r), (cx * s + r, cy * s + r)],
                          fill=(*C["gold"][:3], a))
        
        # 圆框
        draw.ellipse([((cx - circle_r) * s, (cy - circle_r) * s),
                       ((cx + circle_r) * s, (cy + circle_r) * s)],
                      fill=(*C["bg_mid"], 200),
                      outline=(*C["gold"], 90),
                      width=2 * s)
        
        # 编号
        ft_num = _font(18, bold=True)
        draw.text((cx * s - 10 * s, (cy - 28) * s), num,
                  fill=(*C["gold_bright"], 230), font=ft_num)
        
        # 标题
        ft_t = _font(12, bold=True)
        draw.text((cx * s - 45 * s, (cy + 10) * s), step_title,
                  fill=(*C["white"], 230), font=ft_t)
        
        # 描述
        ft_d = _font(9)
        desc_lines = step_desc.split('\n')
        for i, line in enumerate(desc_lines):
            draw.text((cx * s - 60 * s, (cy + 35 + i * 18) * s), line,
                      fill=(*C["text_dim"], 150), font=ft_d)
        
        # 箭头
        if idx < len(steps) - 1:
            next_cx = start_x + spacing * (idx + 1) + spacing // 2
            arrow_sx = (cx + circle_r + 3) * s
            arrow_ex = (next_cx - circle_r - 3) * s
            arrow_cy = cy * s
            draw.line([(arrow_sx, arrow_cy), (arrow_ex, arrow_cy)],
                       fill=(*C["gold_dim"], 50), width=2 * s)
            arrow_size = 7 * s
            draw.polygon([
                (arrow_ex, arrow_cy),
                (arrow_ex - arrow_size, arrow_cy - arrow_size // 2),
                (arrow_ex - arrow_size, arrow_cy + arrow_size // 2),
            ], fill=(*C["gold_dim"], 50))
    
    # 顶部标题
    ft_header = _font(16, bold=True)
    draw.text((W // 2 * s - 90 * s, 18 * s), "➡  三步减少依赖",
              fill=(*C["gold_bright"], 200), font=ft_header)
    
    final = img.resize((W, H), Image.LANCZOS)
    path = OUTPUT_DIR / "inline_三步法_steps.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 步骤插图: {path} ({path.stat().st_size // 1024}KB)")
    return path


def generate_inline_quote():
    """
    金句插图
    尺寸：640×400
    """
    W, H = 640, 400
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    _linear_gradient_v(draw, W, H, C["bg_mid"], C["bg_top"])
    _radial_glow(draw, W // 2, H // 2, 200, C["gold_glow"], 18)
    
    # 左侧竖装饰线
    line_x = 45
    draw.line([(line_x * s, 35 * s), (line_x * s, (H - 35) * s)],
              fill=(*C["gold"], 70), width=3 * s)
    
    # 上引号
    ft_quote_open = _font(52)
    draw.text((60 * s, 28 * s), "❝", fill=(*C["gold"], 50), font=ft_quote_open)
    
    # 金句正文
    lines = [
        "一个系统，胜过二十个工具。",
        "一个大本营，胜过一群帐篷。",
        "少则得，多则惑。",
    ]
    
    ft_body = _font(18, bold=True)
    for i, line in enumerate(lines):
        y_pos = 95 + i * 65
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                draw.text(((75 + dx) * s, (y_pos + dy) * s), line,
                          fill=(*C["gold_glow"], 18), font=ft_body)
        draw.text((75 * s, y_pos * s), line, fill=(*C["gold_bright"], 230), font=ft_body)
    
    # 下引号
    ft_quote_close = _font(52)
    last_line_y = 95 + len(lines) * 65
    draw.text(((W - 100) * s, (last_line_y - 20) * s), "❞",
              fill=(*C["gold"], 50), font=ft_quote_close)
    
    # 底部品牌
    ft_brand = _font(11)
    draw.text(((W // 2 - 40) * s, (H - 35) * s),
              f"—— {BRAND} · {MOTTO}",
              fill=(*C["gold_dim"], 90), font=ft_brand)
    
    final = img.resize((W, H), Image.LANCZOS)
    path = OUTPUT_DIR / "inline_金句_quote.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 金句插图: {path} ({path.stat().st_size // 1024}KB)")
    return path


# ===== 主入口 =====
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"\n{'='*50}")
    print("🎨 觉知岛 ·「SaaS越买越焦虑」专属视觉设计引擎")
    print(f"{'='*50}")
    print(f"超采样倍率: {SCALE}x")
    print(f"设计概念: 由繁入简 (从SaaS焦虑到归一清明)")
    print(f"{'='*50}\n")
    
    # 1. 封面三件套
    cover_path, banner_path, square_path = generate_cover_set()
    
    # 2. 概念插图
    concept_path = generate_inline_concept()
    
    # 3. 步骤插图
    steps_path = generate_inline_steps()
    
    # 4. 金句插图
    quote_path = generate_inline_quote()
    
    print(f"\n{'='*50}")
    print("✅ 全部图片生成完毕！")
    print(f"{'='*50}")
    print(f"📦 输出目录: {OUTPUT_DIR}")
    print(f"   文章封面: 觉知岛_文章封面_900x500.png")
    print(f"   头图横幅: 觉知岛_头图横幅_900x383.png")
    print(f"   分享小图: 觉知岛_分享小图_500x500.png")
    print(f"   概念插图: inline_三大陷阱_concept.png")
    print(f"   步骤插图: inline_三步法_steps.png")
    print(f"   金句插图: inline_金句_quote.png")
    print(f"{'='*50}")
