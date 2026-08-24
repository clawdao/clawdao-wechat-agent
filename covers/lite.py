#!/usr/bin/env python3
"""
「减少依赖，是 2026 年最被低估的竞争力」
专属封面 & 插图 — 超高精度设计引擎（4x超采样）
================================================
设计概念：「破茧·归一」
- 从散乱 SaaS 碎片 → 汇聚为统一系统
- 深空蓝渐变底 × 暖金辉光 = 清明、自由、力量
- 4x 超采样 + 多层渐变 + 辉光文字 + 粒子系统

输出：
  - output/觉知岛_文章封面_900x500.png
  - output/觉知岛_头图横幅_900x383.png
  - output/觉知岛_分享小图_500x500.png
  - output/inline_依赖的三大陷阱_concept.png
  - output/inline_减少依赖三步法_steps.png
  - output/inline_金句_减少依赖_quote.png
"""

import math, os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

random.seed(42)

# ===== 超采样倍率 =====
SCALE = 4  # 4x 超采样，极致抗锯齿

# ===== 输出目录 =====
OUTPUT_DIR = Path("/Users/imfly/Documents/projects/Codex-Agents-运营/公众号自动发布智能体/output")

# ===== 品牌常量 =====
BRAND = "觉知岛"
MOTTO = "知人者智，自知者明"

# ===== 配色方案：「破茧·归一」专属 =====
# 深空蓝 × 暖金 × 纯粹白
C = {
    "bg_top":       (4, 3, 20),      # 顶部深空
    "bg_bottom":    (12, 8, 35),     # 底部深空蓝
    "bg_mid":       (8, 6, 25),      # 中间
    "gold":         (212, 175, 55),  # 主金色
    "gold_bright":  (245, 215, 85),  # 高亮金
    "gold_dim":     (160, 130, 40),  # 暗金
    "gold_glow":    (230, 195, 65),  # 辉光金
    "amber":        (195, 135, 25),  # 琥珀
    "white":        (255, 255, 248), # 主文字白
    "text_dim":     (185, 180, 175), # 副文字
    "scatter":      (170, 145, 70, 25), # 散点
    "accent_blue":  (60, 80, 160, 40),  # 蓝紫光
}

FONT_DIR = Path("/System/Library/Fonts")

def _font(size, bold=False):
    """加载苹方字体"""
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
    """径向辉光圆（从边缘向内渐变）"""
    max_r = radius * SCALE
    cx_s, cy_s = cx * SCALE, cy * SCALE
    for r in range(int(max_r), 0, -2):
        ratio = r / max_r
        a = int(alpha * (1 - ratio))
        if a < 1:
            continue
        draw.ellipse([(cx_s - r, cy_s - r), (cx_s + r, cy_s + r)],
                      fill=(*color[:3], a))

def _soft_circle(draw, cx, cy, radius, color, alpha=40):
    """柔光圆形"""
    s = SCALE
    for r in range(int(radius * s), 0, -4):
        ratio = r / (radius * s)
        a = int(alpha * (1 - ratio) * ratio)
        if a < 2:
            continue
        draw.ellipse([(cx * s - r, cy * s - r), (cx * s + r, cy * s + r)],
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

def _draw_gradient_text(draw, x, y, text, font, c1, c2, w_text=None):
    """绘制渐变填充文字（水平渐变）"""
    s = SCALE
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = (bbox[2] - bbox[0]) if w_text is None else w_text * s
    th = bbox[3] - bbox[1]
    
    # 先绘制白色底
    draw.text((x * s, y * s), text, fill=(255, 255, 255), font=font)
    
    # 再在每个字符上用渐变覆盖
    chars = list(text)
    char_x = x * s
    for ch in chars:
        cb = draw.textbbox((0, 0), ch, font=font)
        cw = cb[2] - cb[0]
        if cw < 1:
            char_x += cw
            continue
        # 字符水平位置比例
        ratio = (char_x - x * s) / max(tw, 1)
        cr = int(c1[0] + (c2[0] - c1[0]) * ratio)
        cg = int(c1[1] + (c2[1] - c1[1]) * ratio)
        cb_c = int(c1[2] + (c2[2] - c1[2]) * ratio)
        draw.text((char_x, y * s + 0), ch, fill=(cr, cg, cb_c), font=font)
        char_x += cw


def _draw_particles(draw, w, h, count=60, area="left"):
    """绘制散落粒子（代表 SaaS 碎片化）"""
    p = C["scatter"]
    s = SCALE
    for _ in range(count):
        if area == "left":
            x = random.randint(20, w // 2 - 10)
            y = random.randint(10, h - 10)
        else:
            x = random.randint(w // 2, w - 10)
            y = random.randint(10, h - 10)
        r = random.choice([0.8, 1.2, 1.6, 2.0, 2.5]) * s
        a = random.randint(5, 25)
        draw.ellipse([(x * s - r, y * s - r), (x * s + r, y * s + r)],
                      fill=(*p[:3], a))


def _draw_converge_paths(draw, w, h, cx_target, cy_target):
    """绘制从左侧散点汇聚到中心的光迹"""
    s = SCALE
    p = C["gold"]
    for _ in range(20):
        sy = random.randint(40, h - 40)
        sx = random.randint(30, w // 3)
        steps = 30
        prev_x, prev_y = None, None
        for t in range(steps + 1):
            ratio = t / steps
            # 贝塞尔-like 曲线
            ctrl_x = (sx + (cx_target - sx) * 0.3 + random.randint(-20, 20))
            ctrl_y = (sy + (cy_target - sy) * 0.15 + random.randint(-15, 15))
            bx = int((1 - ratio)**2 * sx + 2 * (1 - ratio) * ratio * ctrl_x + ratio**2 * cx_target)
            by = int((1 - ratio)**2 * sy + 2 * (1 - ratio) * ratio * ctrl_y + ratio**2 * cy_target)
            a = int(20 * (1 - ratio) * (1 - ratio))
            if a < 1:
                break
            if prev_x is not None:
                draw.line([(prev_x, prev_y), (bx * s, by * s)],
                          fill=(*p, a), width=max(1, int(1.5 * s * (1 - ratio))))
            prev_x, prev_y = bx * s, by * s


def _draw_unity_mandala(draw, cx, cy, r):
    """绘制代表「归一」的曼陀罗圆环"""
    s = SCALE
    colors = [C["gold_dim"], C["gold"], C["gold_bright"]]
    
    # 最外圈辉光
    _radial_glow(draw, cx, cy, r + 25, C["gold_glow"], 30)
    
    # 同心圆环
    for i, mult in enumerate([1.0, 0.82, 0.64, 0.45, 0.28, 0.12]):
        rr = int(r * mult * s)
        if rr < 2:
            continue
        col = colors[i % 3]
        alpha = int(60 + 40 * (1 - abs(mult - 0.5) * 2))
        width = int(max(1, (1.5 + 0.8 * (1 - mult)) * s))
        draw.ellipse([(cx * s - rr, cy * s - rr),
                       (cx * s + rr, cy * s + rr)],
                      outline=(*col, alpha), width=width)
    
    # 中心闪耀
    _radial_glow(draw, cx, cy, int(r * 0.15), C["gold_bright"], 80)
    _radial_glow(draw, cx, cy, int(r * 0.08), (255, 255, 255), 60)
    
    # 射线（从中心向外辐射）
    for angle_deg in range(0, 360, 15):
        rad = math.radians(angle_deg)
        x1 = cx + math.cos(rad) * r * 0.1
        y1 = cy + math.sin(rad) * r * 0.1
        x2 = cx + math.cos(rad) * r * 0.9
        y2 = cy + math.sin(rad) * r * 0.9
        a = random.randint(15, 35)
        draw.line([(x1 * s, y1 * s), (x2 * s, y2 * s)],
                  fill=(*C["gold"], a), width=max(1, int(1.2 * s)))


# ===== 核心封面生成 =====

def generate_cover_set(title_text, subtitle_text):
    """生成封面三件套：文章封面 900×500 + 头图横幅 900×383 + 分享小图 500×500"""
    
    # ── 封面尺寸 ──
    sizes = {
        "cover":   (900, 500),
        "banner":  (900, 383),
        "square":  (500, 500),
    }
    
    # ── 第一步：生成完整封面（最大尺寸） ──
    W, H = sizes["cover"]
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    # 1. 垂直渐变背景
    _linear_gradient_v(draw, W, H, C["bg_top"], C["bg_bottom"])
    
    # 2. 水平渐变叠加（左深右亮）
    _linear_gradient_h(draw, W, H, 
                       (C["bg_top"][0], C["bg_top"][1], C["bg_top"][2], 0),
                       (C["bg_bottom"][0] + 20, C["bg_bottom"][1] + 15, C["bg_bottom"][2] + 40, 0))
    
    # 3. 背景大光晕（右半部）
    _radial_glow(draw, int(W * 0.75), int(H * 0.5), 250, C["accent_blue"], 35)
    _radial_glow(draw, int(W * 0.7), int(H * 0.45), 180, C["gold_glow"], 20)
    
    # 4. 左侧散乱粒子（SaaS 碎片化）
    _draw_particles(draw, W, H, count=50, area="left")
    
    # 5. 汇聚光迹（从左→中心）
    _draw_converge_paths(draw, W, H, int(W * 0.68), int(H * 0.48))
    
    # 6. 右半部的有序粒子（归一后的清明）
    _draw_particles(draw, W, H, count=15, area="right")
    
    # 7. 中心归一曼陀罗圆环
    _draw_unity_mandala(draw, int(W * 0.72), int(H * 0.48), int(min(W, H) * 0.16))
    
    # 8. 标题文字（安全区内：中央 500×500）
    safe_center_x = W // 2  # 450
    safe_top = 0
    safe_bottom = H  # 500
    
    # 标题行分割（主标题+副标题在同一安全区）
    ft_title = _font(26, bold=True)
    ft_sub = _font(14, bold=False)
    ft_brand = _font(10)
    ft_motto = _font(10)
    
    # 主标题：减少依赖，是 2026 年最被低估的竞争力
    title_pos_y = int(H * 0.18)
    
    # 用渐变金绘制标题
    _draw_text_with_glow(draw, safe_center_x - 240, title_pos_y, "减少依赖",
                         ft_title, C["gold_bright"], C["gold_glow"], 60)
    _draw_text_with_glow(draw, safe_center_x - 100, title_pos_y + 50, "是 2026 年",
                         ft_title, C["white"], C["gold_glow"], 30)
    _draw_text_with_glow(draw, safe_center_x - 180, title_pos_y + 100, "最被低估的竞争力",
                         ft_title, C["gold_bright"], C["gold_glow"], 50)
    
    # 副标题：一系统胜万工具
    ft_sub_large = _font(16, bold=True)
    _draw_text_with_glow(draw, safe_center_x - 100, title_pos_y + 170,
                         "一个系统，胜过二十个工具",
                         ft_sub_large, C["gold_dim"], C["gold"], 20)
    
    # 品牌 motto
    _draw_text_with_glow(draw, safe_center_x - 60, int(H * 0.85),
                         f"「{MOTTO}」",
                         ft_motto, C["text_dim"], None, 0)
    
    # 品牌名
    _draw_text_with_glow(draw, safe_center_x - 25, int(H * 0.92),
                         f"—— {BRAND}",
                         ft_motto, C["gold_dim"], None, 0)
    
    # 9. 左下角装饰元素（安全区外）
    draw.line([(10 * s, int(H * 0.85) * s), (10 * s, int(H * 0.95) * s)],
              fill=(*C["gold"], 40), width=2 * s)
    draw.line([(10 * s, int(H * 0.90) * s), (30 * s, int(H * 0.90) * s)],
              fill=(*C["gold"], 40), width=2 * s)
    
    # 10. 右下角装饰线
    draw.line([((W - 10) * s, int(H * 0.85) * s), ((W - 10) * s, int(H * 0.95) * s)],
              fill=(*C["gold"], 25), width=2 * s)
    draw.line([((W - 10) * s, int(H * 0.90) * s), ((W - 30) * s, int(H * 0.90) * s)],
              fill=(*C["gold"], 25), width=2 * s)
    
    # ── 缩放为最终尺寸 ──
    def _resize_smooth(img, size):
        return img.resize(size, Image.LANCZOS)
    
    # ── 保存文章封面 ──
    cover_final = _resize_smooth(img, sizes["cover"])
    cover_path = OUTPUT_DIR / "觉知岛_文章封面_900x500.png"
    cover_final.convert("RGB").save(str(cover_path), "PNG", optimize=True)
    print(f"✅ 文章封面: {cover_path} ({cover_path.stat().st_size // 1024}KB)")
    
    # ── 生成头图横幅 900×383（从封面中心裁剪） ──
    banner_h = 383
    # 从封面中心裁剪 900×383 区域
    crop_top = (H - banner_h) // 2
    banner_img = img.crop((0, crop_top * s, W * s, (crop_top + banner_h) * s))
    banner_final = _resize_smooth(banner_img, (900, 383))
    banner_path = OUTPUT_DIR / "觉知岛_头图横幅_900x383.png"
    banner_final.convert("RGB").save(str(banner_path), "PNG", optimize=True)
    print(f"✅ 头图横幅: {banner_path} ({banner_path.stat().st_size // 1024}KB)")
    
    # ── 生成分享小图 500×500（中心裁剪） ──
    # 安全区 = 中央 500×500
    square = img.crop((200 * s, 0, 700 * s, 500 * s))
    square_final = _resize_smooth(square, (500, 500))
    square_path = OUTPUT_DIR / "觉知岛_分享小图_500x500.png"
    square_final.convert("RGB").save(str(square_path), "PNG", optimize=True)
    print(f"✅ 分享小图: {square_path} ({square_path.stat().st_size // 1024}KB)")
    
    return cover_path, banner_path, square_path


# ===== 内嵌插图生成 =====

def generate_inline_concept():
    """
    概念插图：依赖的三大陷阱
    尺寸：640×400
    设计：三个垂直陷阱柱，从左到右排列
    """
    W, H = 640, 400
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    # 背景渐变
    _linear_gradient_v(draw, W, H, C["bg_top"], C["bg_mid"])
    _radial_glow(draw, W // 2, H // 2, 200, C["accent_blue"], 25)
    
    # 三个陷阱
    traps = [
        ("🧠", "认知税", "注意力被 SaaS 不断消耗"),
        ("🔒", "数据锁", "核心数据在别人服务器"),
        ("📈", "被动涨价", "年年涨价无议价权"),
    ]
    
    spacing = (W - 60) // 3
    start_x = 30
    
    for idx, (icon, trap_title, trap_desc) in enumerate(traps):
        cx = start_x + spacing * idx + spacing // 2
        
        # 陷阱柱（半透明矩形）
        box_w, box_h = spacing - 20, 250
        box_x = cx - box_w // 2
        box_y = 75
        
        # 柱体背景
        draw.rounded_rectangle(
            [(box_x * s, box_y * s), ((box_x + box_w) * s, (box_y + box_h) * s)],
            radius=12 * s,
            fill=(*C["bg_mid"], 180),
            outline=(*C["gold_dim"], 40),
            width=1 * s
        )
        
        # 内部柔和光晕
        _radial_glow(draw, cx, box_y + 50, 60, C["gold_glow"], 15)
        
        # 图标（用文字表示）
        ft_icon = _font(32)
        draw.text((cx * s - 16 * s, (box_y + 15) * s), icon,
                  fill=(*C["gold_bright"], 200), font=ft_icon)
        
        # 标题
        ft_t = _font(14, bold=True)
        draw.text((cx * s - 40 * s, (box_y + 75) * s), trap_title,
                  fill=(*C["gold_bright"], 230), font=ft_t)
        
        # 描述
        ft_d = _font(10)
        draw.text((cx * s - 60 * s, (box_y + 120) * s), trap_desc,
                  fill=(*C["text_dim"], 180), font=ft_d)
        
        # 连接相邻陷阱的小装饰
        if idx < len(traps) - 1:
            next_cx = start_x + spacing * (idx + 1) + spacing // 2
            mid_x = (cx + next_cx) // 2
            draw.line([((cx + box_w // 2 + 5) * s, (box_y + 50) * s),
                        ((next_cx - box_w // 2 - 5) * s, (box_y + 50) * s)],
                       fill=(*C["gold_dim"], 25), width=1 * s)
    
    # 顶部标题
    ft_header = _font(16, bold=True)
    draw.text((W // 2 * s - 90 * s, 15 * s), "⚠  依赖的三大陷阱",
              fill=(*C["gold_bright"], 200), font=ft_header)
    
    # 缩放保存
    final = img.resize((W, H), Image.LANCZOS)
    path = OUTPUT_DIR / "inline_依赖的三大陷阱_concept.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 概念插图: {path} ({path.stat().st_size // 1024}KB)")
    return path


def generate_inline_steps():
    """
    步骤插图：减少依赖三步法
    尺寸：640×400
    设计：水平三步骤，箭头连接，金色主题
    """
    W, H = 640, 400
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    # 背景
    _linear_gradient_v(draw, W, H, C["bg_top"], C["bg_mid"])
    _radial_glow(draw, W // 2, H // 2, 180, C["gold_glow"], 15)
    
    steps = [
        ("①", "盘点依赖清单", "列出每月SaaS支出\n知道自己在依赖什么"),
        ("②", "找到核心场景", "选最痛的环节突破\n不要一次性全替换"),
        ("③", "建立自长系统", "用统一平台替代散装SaaS\n越用越强"),
    ]
    
    spacing = (W - 80) // 3
    start_x = 40
    
    for idx, (num, step_title, step_desc) in enumerate(steps):
        cx = start_x + spacing * idx + spacing // 2
        cy = H // 2 - 10
        
        # 步骤圆
        circle_r = 58
        
        # 背景辉光
        _soft_circle(draw, cx, cy, circle_r + 10, C["gold"], 15)
        
        # 圆框
        draw.ellipse([((cx - circle_r) * s, (cy - circle_r) * s),
                       ((cx + circle_r) * s, (cy + circle_r) * s)],
                      fill=(*C["bg_mid"], 200),
                      outline=(*C["gold"], 100),
                      width=2 * s)
        
        # 编号
        ft_num = _font(18, bold=True)
        draw.text((cx * s - 10 * s, (cy - 25) * s), num,
                  fill=(*C["gold_bright"], 230), font=ft_num)
        
        # 标题
        ft_t = _font(12, bold=True)
        draw.text((cx * s - 48 * s, (cy + 10) * s), step_title,
                  fill=(*C["white"], 230), font=ft_t)
        
        # 描述
        ft_d = _font(9)
        desc_lines = step_desc.split('\n')
        for i, line in enumerate(desc_lines):
            draw.text((cx * s - 60 * s, (cy + 35 + i * 18) * s), line,
                      fill=(*C["text_dim"], 150), font=ft_d)
        
        # 箭头连接到下一步
        if idx < len(steps) - 1:
            next_cx = start_x + spacing * (idx + 1) + spacing // 2
            arrow_sx = (cx + circle_r + 5) * s
            arrow_ex = (next_cx - circle_r - 5) * s
            arrow_cy = cy * s
            
            # 箭头线
            draw.line([(arrow_sx, arrow_cy), (arrow_ex, arrow_cy)],
                       fill=(*C["gold_dim"], 60), width=2 * s)
            # 箭头尖
            arrow_size = 8 * s
            draw.polygon([
                (arrow_ex, arrow_cy),
                (arrow_ex - arrow_size, arrow_cy - arrow_size // 2),
                (arrow_ex - arrow_size, arrow_cy + arrow_size // 2),
            ], fill=(*C["gold_dim"], 60))
    
    # 顶部标题
    ft_header = _font(16, bold=True)
    draw.text((W // 2 * s - 90 * s, 15 * s), "➡  减少依赖三步法",
              fill=(*C["gold_bright"], 200), font=ft_header)
    
    final = img.resize((W, H), Image.LANCZOS)
    path = OUTPUT_DIR / "inline_减少依赖三步法_steps.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 步骤插图: {path} ({path.stat().st_size // 1024}KB)")
    return path


def generate_inline_quote():
    """
    金句插图
    尺寸：640×400
    设计：典雅金句卡片，左右装饰引号
    """
    W, H = 640, 400
    s = SCALE
    img = Image.new("RGBA", (W * s, H * s), C["bg_top"])
    draw = ImageDraw.Draw(img)
    
    # 暖色渐变背景
    _linear_gradient_v(draw, W, H, C["bg_mid"], C["bg_top"])
    _radial_glow(draw, W // 2, H // 2, 200, C["gold_glow"], 20)
    
    # 左侧竖装饰线
    line_x = 45
    draw.line([(line_x * s, 35 * s), (line_x * s, (H - 35) * s)],
              fill=(*C["gold"], 80), width=3 * s)
    
    # 上引号
    ft_quote_open = _font(52)
    draw.text((60 * s, 30 * s), "❝", fill=(*C["gold"], 60), font=ft_quote_open)
    
    # 金句正文
    lines = [
        "一个系统，胜过二十个工具。",
        "一个大本营，胜过一群帐篷。",
        "减少一层依赖，就多一分从容。",
    ]
    
    ft_body = _font(18, bold=True)
    for i, line in enumerate(lines):
        y_pos = 95 + i * 65
        # 文字辉光
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                draw.text(((75 + dx) * s, (y_pos + dy) * s), line,
                          fill=(*C["gold_glow"], 20), font=ft_body)
        draw.text((75 * s, y_pos * s), line, fill=(*C["gold_bright"], 230), font=ft_body)
    
    # 下引号
    ft_quote_close = _font(52)
    last_line_y = 95 + len(lines) * 65
    draw.text(((W - 100) * s, (last_line_y - 20) * s), "❞",
              fill=(*C["gold"], 60), font=ft_quote_close)
    
    # 底部品牌
    ft_brand = _font(11)
    draw.text(((W // 2 - 40) * s, (H - 35) * s),
              f"—— {BRAND} · {MOTTO}",
              fill=(*C["gold_dim"], 100), font=ft_brand)
    
    final = img.resize((W, H), Image.LANCZOS)
    path = OUTPUT_DIR / "inline_金句_减少依赖_quote.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 金句插图: {path} ({path.stat().st_size // 1024}KB)")
    return path


# ===== 主入口 =====
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"\n{'='*50}")
    print("🎨 觉知岛 ·「减少依赖」专属视觉设计引擎")
    print(f"{'='*50}")
    print(f"超采样倍率: {SCALE}x")
    print(f"设计概念: 破茧·归一 (从散乱到统一)")
    print(f"{'='*50}\n")
    
    # 1. 封面三件套
    cover_path, banner_path, square_path = generate_cover_set(
        "减少依赖，是 2026 年最被低估的竞争力",
        "一个系统，胜过二十个工具"
    )
    
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
    print(f"   概念插图: inline_依赖的三大陷阱_concept.png")
    print(f"   步骤插图: inline_减少依赖三步法_steps.png")
    print(f"   金句插图: inline_金句_减少依赖_quote.png")
    print(f"{'='*50}")
