#!/usr/bin/env python3
"""
觉知岛 - 标题背景框图片生成器
生成独立的标题背景框图片（品牌配色+文章标题）
用于放在品牌头图和正文之间
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# ===== 品牌配色方案 =====
BRAND_NAME = "觉知岛"
MOTTO = "知人者智，自知者明"
VALUES = "明道 · 取势 · 优术 · 利他"
TAGLINE = "AI · 区块链 · 认知升级"

TITLE_THEMES = [
    {
        "name": "玄墨金",
        "bg_top": (8, 10, 22),
        "bg_bot": (2, 4, 12),
        "accent": (218, 185, 58),
        "accent_dim": (140, 115, 45),
        "text": (255, 255, 255),
        "text_dim": (180, 175, 170),
    },
    {
        "name": "渊蓝鎏金",
        "bg_top": (6, 10, 24),
        "bg_bot": (2, 4, 14),
        "accent": (210, 180, 68),
        "accent_dim": (120, 100, 50),
        "text": (255, 255, 255),
        "text_dim": (170, 170, 180),
    },
]

def _font(size, bold=True):
    paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def _round_rect(draw, x, y, w, h, r, fill, outline=None, width=1):
    """绘制圆角矩形"""
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=outline, width=width)

def generate_title_banner(title, output_path):
    """生成标题背景框图片 - 900x200"""
    W, H = 900, 200
    
    idx = hash(title) % len(TITLE_THEMES)
    theme = TITLE_THEMES[idx]
    
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 渐变背景
    for y in range(H):
        r = int(theme["bg_top"][0] + (theme["bg_bot"][0] - theme["bg_top"][0]) * y / H)
        g = int(theme["bg_top"][1] + (theme["bg_bot"][1] - theme["bg_top"][1]) * y / H)
        b = int(theme["bg_top"][2] + (theme["bg_bot"][2] - theme["bg_top"][2]) * y / H)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    
    # 圆角矩形边框 - 金色辉光边框
    border_color = (*theme["accent"], 50)
    draw.rounded_rectangle([2, 2, W-3, H-3], radius=16, outline=border_color, width=2)
    
    # 内部浅金色光晕边框
    inner_color = (*theme["accent"], 20)
    draw.rounded_rectangle([6, 6, W-7, H-7], radius=14, outline=inner_color, width=1)
    
    # === 左侧竖线装饰 ===
    draw.line([(28, 30), (28, H-30)], fill=(*theme["accent"], 120), width=2)
    draw.line([(32, 40), (32, H-40)], fill=(*theme["accent"], 30), width=1)
    
    # === 标题文字 ===
    # 标题自动换行
    f_title = _font(36)
    f_title2 = _font(32)
    
    max_w = W - 90
    lines, cur = [], ""
    for ch in title:
        test = cur + ch
        bb = f_title.getbbox(test)
        if bb and bb[2] > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    if not lines:
        lines = ["好文"]
    if len(lines) > 2:
        lines = lines[:2]
        if len(lines[1]) > 22:
            lines[1] = lines[1][:21] + "…"
    
    # 计算标题起始Y
    total_h = len(lines) * 48
    sy = (H - total_h) // 2
    
    for i, line in enumerate(lines):
        ft = f_title if i == 0 else f_title2
        y = sy + i * 48
        
        # 文字背景淡金色条
        bb = ft.getbbox(line)
        tw = bb[2] - bb[0] if bb else 0
        tx = 52
        
        # 文字阴影（微偏移）
        draw.text((tx+1, y+1), line, fill=(0, 0, 0, 60), font=ft)
        # 主文字
        draw.text((tx, y), line, fill=(*theme["text"], 250), font=ft)
    
    # === 右下角觉知岛标识 ===
    f_brand = _font(14)
    brand_x = W - 140
    brand_y = H - 32
    draw.text((brand_x, brand_y), f"◆ {BRAND_NAME}", fill=(*theme["accent"], 140), font=f_brand)
    
    # === 左上角小装饰：金色菱形 ===
    cx, cy = 58, H // 2
    d_size = 4
    diamond = [(cx, cy-d_size), (cx+d_size, cy), (cx, cy+d_size), (cx-d_size, cy)]
    draw.polygon(diamond, fill=(*theme["accent"], 100))
    
    # === 底部金色细装饰线 ===
    draw.line([(45, H-14), (180, H-14)], fill=(*theme["accent"], 30), width=1)
    
    # === 星光点缀 ===
    np.random.seed(abs(hash(title)) & 0xFFFFFFFF)
    for _ in range(12):
        x = np.random.randint(W-200, W-30)
        y = np.random.randint(10, H-10)
        r = np.random.choice([0.8, 1.2, 1.6])
        alpha = np.random.randint(8, 25)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*theme["accent"], alpha))
    
    # 保存
    img.convert("RGB").save(output_path, "PNG", optimize=True)
    print(f"✅ 标题背景框已生成: {output_path}")
    return output_path


def main():
    out_dir = Path("/Users/imfly/Documents/公众号/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    titles = [
        "越焦虑的人 越需要一个觉知系统",
        "你的大脑还在用2G网 换这套认知框架试试",
        "一个人干翻一个团队 秘密是这3个智能体",
    ]
    
    for title in titles:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:30])
        path = out_dir / f"title_banner_{safe}.png"
        generate_title_banner(title, str(path))
    
    print("\n✅ 所有标题背景框生成完成！")


if __name__ == "__main__":
    main()
