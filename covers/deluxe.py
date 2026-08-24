#!/usr/bin/env python3
"""
觉知岛 公众号封面 & 插图 — 高精度优雅设计引擎
================================================
核心优化：
  1. 2x 超采样 → 抗锯齿 + 边缘平滑
  2. 多层渐变叠加（径向 + 线性）
  3. 高级构图：散点→归一 视觉叙事
  4. 渐变填充文字 + 辉光效果
  5. 模块化 inline 插图（3种风格）

用法：
  python3 cover_deluxe.py
"""

import math, json, os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import sys

random.seed(42)

# ===== 品牌常量 =====
BRAND = "觉知岛"
MOTTO = "知人者智，自知者明"
SCALE = 2  # 超采样倍率

# ===== 配色（本篇文章专属定制）=====
PALETTE = {
    "bg_deep":      (4, 3, 10),     # 深底
    "bg_mid":       (8, 6, 18),     # 中间
    "bg_light":     (16, 12, 28),   # 浅底
    "gold":         (218, 185, 60), # 主金色
    "gold_bright":  (245, 215, 85), # 高亮金
    "gold_dim":     (160, 130, 42), # 暗金
    "gold_glow":    (230, 195, 70), # 辉光金
    "amber":        (200, 140, 30), # 琥珀
    "text":         (255, 255, 248),# 主文字
    "text_dim":     (190, 185, 175),# 副文字
    "scatter":      (170, 145, 70, 30), # 散点色
}

FONT_DIR = Path("/System/Library/Fonts")

def _font(size, bold=False):
    name = "PingFang.ttc"
    path = FONT_DIR / name
    if path.exists():
        try:
            return ImageFont.truetype(str(path), size * SCALE)
        except:
            pass
    return ImageFont.load_default()

# ===== 工具函数 =====

def _radial_gradient(draw, cx, cy, r, c1, c2, alpha=255):
    """径向渐变圆"""
    for i in range(r * SCALE, 0, -1):
        ratio = i / (r * SCALE)
        cr = tuple(int(a + (b - a) * (1 - ratio)) for a, b in zip(c1, c2))
        draw.ellipse([(cx - i) * SCALE, (cy - i) * SCALE,
                       (cx + i) * SCALE, (cy + i) * SCALE],
                      fill=(*cr, int(alpha * ratio)))

def _linear_gradient(draw, w, h, c1, c2, vertical=True):
    """线性渐变背景"""
    for y in range(h * SCALE):
        ratio = y / (h * SCALE)
        cr = tuple(int(a + (b - a) * ratio) for a, b in zip(c1, c2))
        draw.line([(0, y), (w * SCALE, y)], fill=cr)

def _glow_circle(draw, cx, cy, r, color, alpha_start=80):
    """辉光圆圈"""
    steps = 20
    for i in range(steps):
        rr = r - (r * i // steps)
        a = alpha_start * (1 - i / steps)
        if a < 1:
            break
        draw.ellipse([(cx - rr) * SCALE, (cy - rr) * SCALE,
                       (cx + rr) * SCALE, (cy + rr) * SCALE],
                      outline=(*color, int(a)), width=max(1, int(2 * SCALE * (1 - i / steps))))

def _draw_text_glow(draw, x, y, text, font, color, glow_color=None):
    """带辉光的文字绘制"""
    if glow_color:
        for dx in range(-2 * SCALE, 3 * SCALE, SCALE):
            for dy in range(-1 * SCALE, 2 * SCALE, SCALE):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, fill=(*glow_color, 60), font=font)
    draw.text((x, y), text, fill=color, font=font)

def _draw_scattered_particles(draw, w, h, count=40):
    """绘制散乱粒子（代表"多"的 SaaS 混乱）"""
    p = PALETTE["scatter"]
    for _ in range(count):
        x = random.randint(30, w // 2 - 20) * SCALE
        y = random.randint(15, h - 15) * SCALE
        r = random.choice([1, 1.5, 2, 2.5, 3]) * SCALE
        a = random.randint(8, 30)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*p[:3], a))

def _draw_converge_lines(draw, w, h, cx_target):
    """从左侧散点区域汇聚到中心的光线"""
    p = PALETTE["gold"]
    cy_center = h // 2
    for _ in range(16):
        sy = random.randint(10, h - 10)
        sx = random.randint(15, w // 3)
        # 曲线汇聚
        steps = 20
        for t in range(steps):
            ratio = t / steps
            x = int((sx + (cx_target - sx) * ratio) * SCALE)
            y = int((sy + (cy_center - sy) * ratio) * SCALE)
            a = int(18 * (1 - ratio))
            if a < 2:
                continue
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(*p, a))

def _draw_unity_circle(draw, w, h, cx, cy, radius):
    """绘制代表「归一」的优雅圆环"""
    # 主圆环 - 多层辉光
    for mult, a, w_mult in [(1.0, 40, 3), (0.92, 25, 2), (0.85, 15, 1.5)]:
        _glow_circle(draw, cx, cy, radius * mult, PALETTE["gold"], a)
    
    # 主圆环线
    rr = int(radius * SCALE)
    for i in range(3):
        r_offset = rr + (i - 1) * 3 * SCALE
        if r_offset < 5:
            continue
        draw.ellipse([(cx * SCALE - r_offset, cy * SCALE - r_offset),
                       (cx * SCALE + r_offset, cy * SCALE + r_offset)],
                      outline=(*PALETTE["gold"], 80 + 40 * (1 - abs(i - 1))), width=max(1, 2 * SCALE - i * SCALE))
    
    # 中心光晕
    _radial_gradient(draw, cx, cy, 8, PALETTE["gold_bright"], PALETTE["bg_deep"], 60)
    
    # 内圆装饰（极简）
    rr_inner = int(radius * 0.6 * SCALE)
    draw.ellipse([(cx * SCALE - rr_inner, cy * SCALE - rr_inner),
                   (cx * SCALE + rr_inner, cy * SCALE + rr_inner)],
                  outline=(*PALETTE["gold_dim"], 60), width=1 * SCALE)

def _draw_title_text(draw, w, h, title_text):
    """绘制标题文字（安全区内居中，2x超采样）"""
    s = SCALE
    SAFE_LEFT = 200
    SAFE_RIGHT = 700
    SAFE_CX = (SAFE_LEFT + SAFE_RIGHT) // 2

    # 标题分两行
    f_size = 38
    ft = _font(f_size, bold=True)
    
    # 智能分行
    max_w = (SAFE_RIGHT - SAFE_LEFT - 40) * s
    lines = []
    for part in title_text:
        test = "".join([part])
        bb = ft.getbbox(test)
        if bb and (bb[2] - bb[0]) > max_w:
            if lines:
                lines[-1] = lines[-1] + part
            else:
                # 强制分行
                mid = len(part) // 2
                lines.append(part[:mid])
                lines.append(part[mid:])
        else:
            if lines:
                lines[-1] = lines[-1] + part
            else:
                lines.append(part)
    
    # 如果手动分
    title_str = "".join(title_text)
    if len(title_str) > 14:
        # 尝试在标点处分行
        split_chars = ["？", "，", "；", "。", "！", ",", "?", ";"]
        split_pos = -1
        for i, ch in enumerate(title_str):
            if ch in split_chars and i < len(title_str) - 2 and i > 3:
                split_pos = i + 1
                break
        if split_pos > 0:
            lines = [title_str[:split_pos], title_str[split_pos:]]
        else:
            mid = len(title_str) // 2
            lines = [title_str[:mid], title_str[mid:]]
    else:
        lines = [title_str]

    if len(lines) > 2:
        lines = lines[:2]
    
    # 计算位置
    lh = ft.getbbox("测")[3] + 10 * s
    th = len(lines) * lh
    sy = (h * s - th) // 2 - 20 * s
    
    for i, line in enumerate(lines):
        y = sy + i * lh
        bb = ft.getbbox(line)
        lw = (bb[2] - bb[0])
        lx = SAFE_CX * s - lw // 2
        
        # 辉光
        _draw_text_glow(draw, lx, y, line, ft, 
                       (*PALETTE["text"], 248), PALETTE["gold_glow"])
    
    # 底部副标题
    sub_text = f"「 {MOTTO} 」"
    ft_sub = _font(13)
    bb_sub = ft_sub.getbbox(sub_text)
    sw = (bb_sub[2] - bb_sub[0])
    sx = SAFE_CX * s - sw // 2
    sy_sub = sy + len(lines) * lh + 35 * s
    draw.text((sx, sy_sub), sub_text, fill=(*PALETTE["gold_dim"], 200), font=ft_sub)

def generate_deluxe_cover(title_str, topic=""):
    """生成高精度封面（900×500 文章封面 + 900×383 头图 + 500×500 分享图）"""
    s = SCALE
    
    # ===== 1. 文章封面 900×500（超采样 1800×1000）=====
    W, H = 900, 500
    img = Image.new("RGBA", (W * s, H * s), PALETTE["bg_deep"])
    draw = ImageDraw.Draw(img)
    
    # 2. 多层渐变背景
    # 底层：从上到下渐变
    _linear_gradient(draw, W, H, PALETTE["bg_deep"], PALETTE["bg_mid"])
    # 第二层：中心辐射
    _radial_gradient(draw, W // 2, H // 2, 220, PALETTE["bg_light"], PALETTE["bg_deep"], 40)
    # 第三层：右侧暖光（金色辉光隐隐透出）
    _radial_gradient(draw, 750, H // 2, 180, PALETTE["gold_glow"], PALETTE["bg_deep"], 30)
    
    # 3. 左侧散点（"多"——SaaS 混乱）
    _draw_scattered_particles(draw, W, H, 50)
    
    # 4. 汇聚光线（从散点到中心）
    _draw_converge_lines(draw, W, H, 450)
    
    # 5. 右侧归一圆环（"一"——ClawDao）
    _draw_unity_circle(draw, W, H, 680, H // 2, 65)
    
    # 6. 顶部品牌名
    brand_text = f"◆ {BRAND}"
    ft_brand = _font(14)
    bb_br = ft_brand.getbbox(brand_text)
    bw = bb_br[2] - bb_br[0]
    cx = (200 + 700) // 2
    draw.text((cx * s - bw // 2, 25 * s), brand_text, fill=(*PALETTE["gold"], 220), font=ft_brand)
    # 装饰线
    draw.line([((cx - 20) * s, 48 * s), ((cx + 20) * s, 48 * s)], fill=(*PALETTE["gold"], 100), width=s)
    draw.line([((cx - 14) * s, 51 * s), ((cx + 14) * s, 51 * s)], fill=(*PALETTE["gold"], 45), width=s)
    
    # 7. 标题
    _draw_title_text(draw, W, H, list(title_str))
    
    # 8. 底部 Tagline
    tag = "AI · 认知升级 · 顺道而为"
    ft_tag = _font(12)
    bb_tag = ft_tag.getbbox(tag)
    tw = bb_tag[2] - bb_tag[0]
    tx = cx * s - tw // 2
    draw.text((tx, (H - 28) * s), tag, fill=(*PALETTE["text_dim"], 160), font=ft_tag)
    
    # ===== 降采样（2x → 1x）=====
    final = img.resize((W, H), Image.LANCZOS)
    
    out_dir = Path("./output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in title_str[:20])
    
    # 保存文章封面 900×500
    cover_path = out_dir / f"cover_{safe_name}_900x500.png"
    final.convert("RGB").save(str(cover_path), "PNG", optimize=True)
    print(f"✅ 文章封面 900×500: {cover_path}")
    
    # 生成头图横幅 900×383（从顶部裁剪）
    banner = final.crop((0, 0, 900, 383))
    banner_path = out_dir / f"觉知岛_头图横幅_900x383.png"
    banner.convert("RGB").save(str(banner_path), "PNG", optimize=True)
    print(f"✅ 头图横幅 900×383: {banner_path}")
    
    # 生成分享小图 500×500（中心裁剪）
    square = final.crop((200, 0, 700, 500))
    square_resized = square.resize((500, 500), Image.LANCZOS)
    share_path = out_dir / f"觉知岛_分享小图_500x500.png"
    square_resized.convert("RGB").save(str(share_path), "PNG", optimize=True)
    print(f"✅ 分享小图 500×500: {share_path}")
    
    return cover_path, banner_path, share_path


# ===== Inline 插图生成 =====

def _draw_inline_bg(draw, w, h, theme_variant="gold"):
    """插图通用背景"""
    pal = PALETTE
    _linear_gradient(draw, w, h, pal["bg_deep"], pal["bg_mid"])
    _radial_gradient(draw, w // 2, h // 2, min(w, h) // 3, pal["bg_light"], pal["bg_deep"], 30)

def generate_inline_concept(title, concept_items=None):
    """概念图插图 — 640×400"""
    s = SCALE
    W, H = 640, 400
    img = Image.new("RGBA", (W * s, H * s), PALETTE["bg_deep"])
    draw = ImageDraw.Draw(img)
    
    _draw_inline_bg(draw, W, H)
    
    # 三个概念节点
    if not concept_items:
        concept_items = [
            ("认知税", "注意力被 SaaS 消耗"),
            ("数据锁", "数据在别人服务器"),
            ("被动涨价", "年年涨无议价权"),
        ]
    
    positions = [(W // 2, H // 2 - 60), (W // 2 - 120, H // 2 + 50), (W // 2 + 120, H // 2 + 50)]
    
    # 连接线
    for i in range(3):
        for j in range(i + 1, 3):
            draw.line([(positions[i][0] * s, positions[i][1] * s),
                       (positions[j][0] * s, positions[j][1] * s)],
                      fill=(*PALETTE["gold_dim"], 20), width=s)
    
    # 中心大圆（三个陷阱的核心）
    _radial_gradient(draw, W // 2, H // 2, 18, PALETTE["amber"], PALETTE["bg_deep"], 30)
    draw.ellipse([(W // 2 - 10) * s, (H // 2 - 10) * s, (W // 2 + 10) * s, (H // 2 + 10) * s],
                 outline=(*PALETTE["amber"], 50), width=s)
    
    # 三个节点
    for idx, ((px, py), (name, desc)) in enumerate(zip(positions, concept_items)):
        r = 55 * s
        draw.ellipse([(px * s - r, py * s - r), (px * s + r, py * s + r)],
                     fill=(*PALETTE["bg_deep"], 180), outline=(*PALETTE["gold"], 80), width=s)
        
        ft_name = _font(12, bold=True)
        ft_desc = _font(9)
        draw.text((px * s - 35 * s, py * s - 15 * s), name, fill=(*PALETTE["gold_bright"], 230), font=ft_name)
        draw.text((px * s - 45 * s, py * s + 10 * s), desc, fill=(*PALETTE["text_dim"], 150), font=ft_desc)
    
    # 底部小字
    ft_sub = _font(10)
    draw.text((W // 2 * s - 50 * s, (H - 30) * s), "依赖的三大陷阱", fill=(*PALETTE["gold_dim"], 120), font=ft_sub)
    
    final = img.resize((W, H), Image.LANCZOS)
    out_dir = Path("./output")
    path = out_dir / "inline_三大陷阱_concept.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 概念插图: {path}")
    return path

def generate_inline_steps(title, step_items=None):
    """步骤图插图 — 640×400"""
    s = SCALE
    W, H = 640, 400
    img = Image.new("RGBA", (W * s, H * s), PALETTE["bg_deep"])
    draw = ImageDraw.Draw(img)
    
    _draw_inline_bg(draw, W, H)
    
    if not step_items:
        step_items = [
            ("1", "盘点清单", "列出每月 SaaS 支出"),
            ("2", "找到场景", "选最痛点突破"),
            ("3", "建立系统", "替代碎片化 SaaS"),
        ]
    
    # 横向步骤连接线
    total_steps = len(step_items)
    spacing = (W - 60) // total_steps
    
    for idx, (num, title_item, desc) in enumerate(step_items):
        cx = 30 + spacing * idx + spacing // 2
        cy = H // 2 - 10
        
        # 圆
        r = 50 * s
        # 辉光
        _radial_gradient(draw, cx, cy, 20, PALETTE["gold_glow"], PALETTE["bg_deep"], 25)
        draw.ellipse([(cx * s - r, cy * s - r), (cx * s + r, cy * s + r)],
                     fill=(*PALETTE["bg_deep"], 200), outline=(*PALETTE["gold"], 100), width=2 * s)
        
        # 编号
        ft_num = _font(18, bold=True)
        draw.text((cx * s - 8 * s, cy * s - 18 * s), num, fill=(*PALETTE["gold_bright"], 240), font=ft_num)
        
        # 标题
        ft_t = _font(11, bold=True)
        draw.text((cx * s - 40 * s, cy * s + 15 * s), title_item, fill=(*PALETTE["text"], 230), font=ft_t)
        
        # 描述
        ft_d = _font(9)
        draw.text((cx * s - 50 * s, cy * s + 38 * s), desc, fill=(*PALETTE["text_dim"], 140), font=ft_d)
        
        # 连接箭头
        if idx < total_steps - 1:
            next_cx = 30 + spacing * (idx + 1) + spacing // 2
            draw.line([((cx + 52) * s, cy * s), ((next_cx - 52) * s, cy * s)],
                     fill=(*PALETTE["gold_dim"], 40), width=2 * s)
            # 箭头尖
            arrow_x = (next_cx - 52) * s
            draw.polygon([(arrow_x, cy * s), (arrow_x - 8 * s, cy * s - 5 * s),
                          (arrow_x - 8 * s, cy * s + 5 * s)],
                         fill=(*PALETTE["gold_dim"], 40))
    
    final = img.resize((W, H), Image.LANCZOS)
    out_dir = Path("./output")
    path = out_dir / "inline_三步法_steps.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 步骤插图: {path}")
    return path

def generate_inline_quote(quote_text):
    """金句图插图 — 640×400"""
    s = SCALE
    W, H = 640, 400
    img = Image.new("RGBA", (W * s, H * s), PALETTE["bg_deep"])
    draw = ImageDraw.Draw(img)
    
    # 特殊背景：更暖的辉光
    _linear_gradient(draw, W, H, PALETTE["bg_deep"], PALETTE["bg_mid"])
    _radial_gradient(draw, W // 2, H // 2, 160, PALETTE["gold_glow"], PALETTE["bg_deep"], 35)
    
    # 左装饰线
    draw.line([(40 * s, 30 * s), (40 * s, (H - 30) * s)], fill=(*PALETTE["gold"], 80), width=3 * s)
    
    # 上引号
    ft_quote = _font(48)
    draw.text((60 * s, 45 * s), "「", fill=(*PALETTE["gold"], 50), font=ft_quote)
    
    # 金句正文
    lines = quote_text.split("\n") if quote_text else ["一个系统，胜过二十个工具，", "一个大本营，胜过一群帐篷。"]
    ft = _font(16)
    for i, line in enumerate(lines):
        y_pos = 100 + i * 55
        draw.text((70 * s, y_pos * s), line, fill=(*PALETTE["gold_bright"], 230), font=ft)
    
    # 下引号
    ft_quote_end = _font(48)
    end_y = 100 + len(lines) * 55
    draw.text((W * s - 70 * s, (end_y - 5) * s), "」", fill=(*PALETTE["gold"], 50), font=ft_quote_end)
    
    # 底部品牌
    ft_brand = _font(11)
    draw.text((W // 2 * s - 35 * s, (H - 30) * s), f"—— {BRAND}", fill=(*PALETTE["gold_dim"], 100), font=ft_brand)
    
    final = img.resize((W, H), Image.LANCZOS)
    out_dir = Path("./output")
    path = out_dir / "inline_金句_quote.png"
    final.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ 金句插图: {path}")
    return path


# ===== 主入口 =====
if __name__ == "__main__":
    title = "SaaS越买越焦虑？少则得多则惑"
    
    # 1. 封面三件套
    generate_deluxe_cover(title, "认知升级")
    
    # 2. 概念插图
    generate_inline_concept(
        "依赖的三大陷阱",
        [("认知税", "注意力被 SaaS 消耗"), ("数据锁", "数据在别人服务器"), ("被动涨价", "年年涨无议价权")]
    )
    
    # 3. 步骤插图
    generate_inline_steps(
        "减少依赖三步法",
        [("1", "盘点清单", "列出每月SaaS支出"), ("2", "找到场景", "选最痛点突破"), ("3", "建立系统", "替代碎片化SaaS")]
    )
    
    # 4. 金句插图
    generate_inline_quote("一个系统，胜过二十个工具。\n一个大本营，胜过一群帐篷。")
    
    print("\n🎨 全部图片已生成！")
