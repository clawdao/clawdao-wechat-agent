#!/usr/bin/env python3
"""
觉知岛 公众号高质量图片生成器（增强版）
生成更精美的封面图、配图，替代原有的简陋 PIL 生成
"""

import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pathlib import Path
import sys
sys.path.insert(0, '/Users/imfly/Documents/公众号')

random.seed(42)
np.random.seed(42)

# ===== 品牌配色方案（更丰富）=====
BRAND_THEMES = [
    # 玄墨金 - 深邃智慧
    {
        "name": "玄墨金",
        "bg_primary": (5, 8, 20),
        "bg_secondary": (15, 12, 30),
        "accent": (218, 185, 60),
        "accent_light": (255, 220, 100),
        "accent_dim": (160, 130, 40),
        "text": (255, 255, 255),
        "text_dim": (200, 195, 190),
        "glow": (218, 185, 60),
        "particle": (255, 215, 0),
    },
    # 烟霞紫 - AI科技感
    {
        "name": "烟霞紫",
        "bg_primary": (12, 6, 28),
        "bg_secondary": (25, 12, 40),
        "accent": (180, 120, 255),
        "accent_light": (210, 170, 255),
        "accent_dim": (120, 80, 180),
        "text": (255, 255, 255),
        "text_dim": (195, 185, 210),
        "glow": (180, 120, 255),
        "particle": (200, 160, 255),
    },
    # 渊蓝鎏金 - 沉稳力量
    {
        "name": "渊蓝鎏金",
        "bg_primary": (4, 10, 30),
        "bg_secondary": (8, 20, 45),
        "accent": (200, 175, 65),
        "accent_light": (240, 215, 100),
        "accent_dim": (130, 115, 50),
        "text": (255, 255, 255),
        "text_dim": (180, 190, 210),
        "glow": (200, 175, 65),
        "particle": (220, 200, 100),
    },
    # 檀褐赤金 - 温润厚重
    {
        "name": "檀褐赤金",
        "bg_primary": (12, 8, 10),
        "bg_secondary": (25, 14, 12),
        "accent": (215, 165, 50),
        "accent_light": (250, 195, 80),
        "accent_dim": (140, 105, 35),
        "text": (255, 255, 255),
        "text_dim": (195, 185, 175),
        "glow": (215, 165, 50),
        "particle": (240, 190, 80),
    },
    # 翠微青 - 科技成长
    {
        "name": "翠微青",
        "bg_primary": (6, 18, 12),
        "bg_secondary": (10, 28, 18),
        "accent": (80, 220, 160),
        "accent_light": (120, 255, 190),
        "accent_dim": (50, 150, 110),
        "text": (255, 255, 255),
        "text_dim": (180, 210, 195),
        "glow": (80, 220, 160),
        "particle": (120, 240, 180),
    },
]

BRAND_NAME = "觉知岛"
TAGLINE = "AI · 区块链 · 认知升级"
MOTTO = "知人者智，自知者明"
VALUES = "明道 · 取势 · 优术 · 利他"
OUTPUT_DIR = Path("/Users/imfly/Documents/公众号/output")


def _font(size, bold=False):
    """加载字体，支持粗体"""
    paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    if bold:
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


def _blend_color(c1, c2, ratio):
    """混合两种颜色"""
    return tuple(int(a + (b - a) * ratio) for a, b in zip(c1, c2))


def _draw_gradient(draw, w, h, c1, c2, vertical=True):
    """绘制渐变背景"""
    steps = h if vertical else w
    for i in range(steps):
        ratio = i / steps
        color = _blend_color(c1, c2, ratio)
        if vertical:
            draw.line([(0, i), (w, i)], fill=color)
        else:
            draw.line([(i, 0), (i, h)], fill=color)


def _draw_circle_gradient(draw, cx, cy, r, c1, c2, alpha=60):
    """绘制径向渐变圆"""
    for i in range(r, 0, -1):
        ratio = i / r
        color = _blend_color(c1, c2, 1 - ratio)
        a = int(alpha * (1 - ratio * ratio))
        draw.ellipse([cx-i, cy-i, cx+i, cy+i], fill=(*color, a))


def _draw_particles(draw, w, h, theme, count=60):
    """绘制粒子/星点"""
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.choice([0.5, 0.8, 1.2, 1.5, 2.0])
        alpha = random.randint(15, 60)
        color = _blend_color(theme["particle"], (255, 255, 255), random.random() * 0.5)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*color, alpha))


def _draw_connection_lines(draw, w, h, theme, count=12):
    """绘制连接线（科技感）"""
    points = [(random.randint(50, w-50), random.randint(50, h-50)) for _ in range(count)]
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            dist = math.sqrt((points[i][0]-points[j][0])**2 + (points[i][1]-points[j][1])**2)
            if dist < 250:
                alpha = int(8 * (1 - dist / 250))
                draw.line([points[i], points[j]], fill=(*theme["accent"], alpha), width=1)


def _draw_grid_overlay(draw, w, h, theme):
    """绘制科技网格"""
    step = 60
    for x in range(0, w, step):
        alpha = random.randint(2, 4)
        draw.line([(x, 0), (x, h)], fill=(*theme["accent"], alpha), width=1)
    for y in range(0, h, step):
        alpha = random.randint(2, 4)
        draw.line([(0, y), (w, y)], fill=(*theme["accent"], alpha), width=1)


def _draw_abstract_waves(draw, w, h, theme):
    """绘制抽象波浪/数据流"""
    for wave_idx in range(3):
        points = []
        offset_y = h * (0.3 + wave_idx * 0.2)
        amp = 15 + wave_idx * 5
        for x in range(0, w+5, 5):
            y = offset_y + math.sin(x * 0.02 + wave_idx * 1.5) * amp + math.sin(x * 0.05 + wave_idx) * 5
            points.append((x, y))
        alpha = 6 - wave_idx * 1
        draw.line(points, fill=(*theme["accent"], alpha), width=2)


def _draw_zen_circle(draw, cx, cy, r, theme):
    """绘制禅意圆（半透明同心圆）"""
    for radius in range(r, 5, -5):
        alpha = max(2, 30 - (r - radius) // 2)
        draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius],
                     outline=(*theme["accent"], alpha), width=1)


def _draw_geometric_pattern(draw, w, h, theme):
    """绘制几何装饰图案"""
    # 左上角装饰
    cx, cy = 60, 60
    for r in range(10, 50, 5):
        alpha = 10 - (r // 10)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(*theme["accent"], max(2, alpha)), width=1)
    draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill=(*theme["accent_light"], 80))

    # 右下角装饰
    cx2, cy2 = w-50, h-50
    for r in range(15, 55, 5):
        alpha = 8 - (r // 10)
        draw.ellipse([cx2-r, cy2-r, cx2+r, cy2+r], outline=(*theme["accent"], max(2, alpha)), width=1)


def _draw_ai_node_network(draw, w, h, theme):
    """绘制AI节点网络（适合科技类文章）"""
    nodes = [
        (w//2-80, 40, 40), (w//2+60, 50, 35), (w//2-30, 90, 30),
        (w//2+90, 100, 25), (w//2-100, 80, 20),
    ]
    for x, y, r in nodes:
        for rad in range(r, 0, -3):
            a = max(3, 15 - (r - rad) // 2)
            draw.ellipse([x-rad, y-rad, x+rad, y+rad], fill=(*theme["accent_light"], a))
        draw.ellipse([x-2, y-2, x+2, y+2], fill=(*theme["accent"], 200))

    # 连接线
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            dist = math.sqrt((nodes[i][0]-nodes[j][0])**2 + (nodes[i][1]-nodes[j][1])**2)
            if dist < 160:
                alpha = 8
                draw.line([(nodes[i][0], nodes[i][1]), (nodes[j][0], nodes[j][1])],
                          fill=(*theme["accent"], alpha), width=1)


def _draw_brand_badge(draw, x, y, theme):
    """绘制品牌徽标"""
    # 小圆点装饰
    draw.ellipse([x, y, x+6, y+6], fill=(*theme["accent"], 220))
    draw.ellipse([x+10, y-2, x+14, y+2], fill=(*theme["accent_light"], 150))
    draw.ellipse([x+18, y+2, x+20, y+4], fill=(*theme["accent_dim"], 100))


def _title_to_lines(title, font, max_w):
    """将标题按宽度拆分为多行"""
    lines, cur = [], ""
    for ch in title:
        test = cur + ch
        bb = font.getbbox(test)
        if bb and bb[2] > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    if not lines:
        lines = ["好文"]
    return lines


def _draw_title_text(draw, x, y, lines, font, theme, shadow_offset=2):
    """绘制标题文字（带发光阴影效果）"""
    line_h = font.getbbox("测")[3] + 15
    for i, line in enumerate(lines):
        ly = y + i * line_h
        # 阴影层
        draw.text((x+shadow_offset, ly+shadow_offset), line, fill=(0, 0, 0, 80), font=font)
        # 主文字
        draw.text((x, ly), line, fill=(*theme["text"], 250), font=font)
        # 下划线装饰（针对最后一行或第一行）
        if i == len(lines) - 1:
            bb = font.getbbox(line)
            line_w = bb[2]
            draw.line([(x, ly+line_h-2), (x+line_w, ly+line_h-2)],
                      fill=(*theme["accent"], 100), width=1)


def generate_cover_enhanced(title, topic="", keywords=None):
    """
    生成高质量封面图
    返回: (Path) 图片路径
    """
    W, H = 900, 383

    # 基于主题选择配色
    theme_map = {
        "认知升级": 0,
        "区块链": 1,
        "AI": 1,
        "副业": 3,
        "创业": 3,
        "成长": 4,
        "科技": 1,
        "效率": 4,
        "默认": 0,
    }
    theme_idx = 0
    for key, idx in theme_map.items():
        if key in topic or key in (keywords or []):
            theme_idx = idx
            break
    theme = BRAND_THEMES[theme_idx]

    img = Image.new("RGBA", (W, H), theme["bg_primary"])
    draw = ImageDraw.Draw(img, "RGBA")

    # ===== 1. 渐变背景 =====
    _draw_gradient(draw, W, H, theme["bg_primary"], theme["bg_secondary"])

    # ===== 2. 背景光晕 =====
    _draw_circle_gradient(draw, W//2, H//2, 200, theme["glow"], theme["bg_primary"], 15)
    _draw_circle_gradient(draw, W-100, H-80, 120, theme["accent_light"], theme["bg_secondary"], 8)
    _draw_circle_gradient(draw, 80, 50, 100, theme["glow"], theme["bg_primary"], 10)

    # ===== 3. 科技网格 =====
    _draw_grid_overlay(draw, W, H, theme)

    # ===== 4. 抽象波浪 =====
    _draw_abstract_waves(draw, W, H, theme)

    # ===== 5. 粒子系统 =====
    _draw_particles(draw, W, H, theme, 50)

    # ===== 6. 连接线 =====
    _draw_connection_lines(draw, W, H, theme, 10)

    # ===== 7. 几何图案 =====
    _draw_geometric_pattern(draw, W, H, theme)

    # ===== 8. AI 节点网络 =====
    _draw_ai_node_network(draw, W, H, theme)

    # ===== 9. 禅意圆 =====
    _draw_zen_circle(draw, W-120, H-80, 40, theme)

    # ===== 10. 品牌徽标 =====
    _draw_brand_badge(draw, 22, 15, theme)
    draw.text((30, 12), f"◆ {BRAND_NAME}", fill=(*theme["accent"], 240), font=_font(16, bold=True))

    # 装饰线
    y_line = 38
    draw.line([(22, y_line), (70, y_line)], fill=(*theme["accent"], 140), width=1)
    draw.line([(22, y_line+3), (56, y_line+3)], fill=(*theme["accent"], 50), width=1)

    # ===== 11. 标题文字 =====
    title_font_size = 42 if len(title) <= 8 else 36 if len(title) <= 12 else 32
    f_title = _font(title_font_size, bold=True)

    # 拆分标题
    max_w = W - 170
    lines = _title_to_lines(title, f_title, max_w)
    if len(lines) > 2:
        f_title = _font(30, bold=True)
        lines = _title_to_lines(title, f_title, max_w)
        if len(lines) > 2:
            lines = lines[:2]

    # 标题位置 - 偏左下区域
    title_x = 26
    line_h = f_title.getbbox("测")[3] + 12
    total_h = len(lines) * line_h
    title_y = max(55, (H - total_h - 60) // 2 + 5)

    _draw_title_text(draw, title_x, title_y, lines, f_title, theme, shadow_offset=2)

    # ===== 12. 道德经金句 =====
    motto_y = title_y + len(lines) * line_h + 16
    draw.text((26, motto_y), f"「 {MOTTO} 」", fill=(*theme["accent"], 200), font=_font(15))

    # ===== 13. 分隔线 =====
    line2_y = motto_y + 28
    draw.line([(26, line2_y), (72, line2_y)], fill=(*theme["accent"], 130), width=1)
    draw.line([(26, line2_y+3), (54, line2_y+3)], fill=(*theme["accent"], 50), width=1)

    # ===== 14. 价值观 =====
    val_y = line2_y + 14
    draw.text((26, val_y), VALUES, fill=(*theme["accent"], 160), font=_font(14))

    # ===== 15. 底部标签 =====
    tag_y = H - 26
    draw.text((26, tag_y), TAGLINE, fill=(*theme["text_dim"], 180), font=_font(13))

    # ===== 16. 底部装饰线 =====
    draw.line([(26, H-8), (W-26, H-8)], fill=(*theme["accent"], 12), width=1)

    # ===== 保存 =====
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:25])
    path = OUTPUT_DIR / f"cover_{safe_name}.png"
    img.convert("RGB").save(path, "PNG", optimize=True)
    print(f"✅ 封面图已生成（增强版）: {path} (配色: {theme['name']})")
    return path


def generate_inline_image(title, style="diagram", topic="", width=640, height=400,
                               content_lines=None, step_items=None, concept_items=None, quote_text=None):
    """
    生成文章内部插图
    style: diagram/info/quote/concept/steps
    content_lines: 文章内容列表，用于提取实际内容
    step_items: 步骤图的自定义步骤项 [(编号, 标题, 描述)]
    concept_items: 概念图的自定义概念项 [(名称, 说明)]
    quote_text: 金句图的自定义金句文本
    返回: (Path) 图片路径
    """
    W, H = width, height

    theme_idx = hash(topic or title) % len(BRAND_THEMES)
    theme = BRAND_THEMES[theme_idx]

    img = Image.new("RGBA", (W, H), theme["bg_primary"])
    draw = ImageDraw.Draw(img, "RGBA")

    # ===== 渐变背景 =====
    _draw_gradient(draw, W, H, theme["bg_primary"], theme["bg_secondary"])

    # ===== 根据样式绘制不同内容 =====
    if style == "diagram":
        # 流程图/示意图风格
        _draw_grid_overlay(draw, W, H, theme)
        _draw_particles(draw, W, H, theme, 20)

        nodes_data = [
            (80, H//2-30, "观察", "Observe"),
            (W//2, H//2-60, "定位", "Position"),
            (W-80, H//2-30, "设计", "Design"),
        ]
        for idx, (nx, ny, cn, en) in enumerate(nodes_data):
            box_w, box_h = 120, 50
            _draw_circle_gradient(draw, nx, ny+10, 40, theme["accent_light"], theme["bg_primary"], 20)
            draw.rounded_rectangle(
                [nx-box_w//2, ny-box_h//2, nx+box_w//2, ny+box_h//2],
                radius=8,
                fill=(*theme["bg_primary"], 180),
                outline=(*theme["accent"], 120),
                width=1
            )
            draw.text((nx-30, ny-12), cn, fill=(*theme["accent_light"], 230), font=_font(16, bold=True))
            draw.text((nx-25, ny+10), en, fill=(*theme["text_dim"], 150), font=_font(10))

            if idx < len(nodes_data) - 1:
                nx2, ny2 = nodes_data[idx+1][0], nodes_data[idx+1][1]
                draw.line([(nx+box_w//2, ny), (nx2-box_w//2, ny2)],
                          fill=(*theme["accent"], 40), width=2)
                # 箭头
                mid_x, mid_y = (nx+nx2)//2, (ny+ny2)//2
                draw.polygon([(mid_x, mid_y-5), (mid_x+8, mid_y), (mid_x, mid_y+5)],
                            fill=(*theme["accent"], 50))

        draw.text((W//2-30, H-25), "OPD 核心流程", fill=(*theme["text_dim"], 100), font=_font(11))

    elif style == "info":
        # 信息卡片风格
        _draw_particles(draw, W, H, theme, 15)
        _draw_circle_gradient(draw, W//2, H//2, 130, theme["glow"], theme["bg_primary"], 8)
        _draw_particles(draw, W, H, theme, 15)
        _draw_circle_gradient(draw, W//2, H//2, 130, theme["glow"], theme["bg_primary"], 8)

        data_items = [
            ("产品系统", "AI 接管代码与迭代"),
            ("交易系统", "流量自动获取与转化"),
            ("组织系统", "Agent 虚拟团队"),
            ("分配系统", "收益自动分账"),
        ]
        box_w = (W-80) // 2
        for idx, (item_title, item_desc) in enumerate(data_items):
            col, row = idx % 2, idx // 2
            bx = 20 + col * (box_w + 20)
            by = 40 + row * 100
            draw.rounded_rectangle(
                [bx, by, bx+box_w-10, by+85],
                radius=10,
                fill=(*theme["bg_secondary"], 180),
                outline=(*theme["accent"], 60),
                width=1
            )
            # 编号
            draw.ellipse([bx+10, by+10, bx+24, by+24], fill=(*theme["accent"], 150))
            draw.text((bx+14, by+12), str(idx+1), fill=(*theme["bg_primary"], 220), font=_font(12, bold=True))
            draw.text((bx+32, by+12), item_title, fill=(*theme["accent_light"], 220), font=_font(15, bold=True))
            draw.text((bx+14, by+42), item_desc, fill=(*theme["text_dim"], 180), font=_font(13))

        draw.text((W//2-40, H-25), "OPD 四系统", fill=(*theme["text_dim"], 100), font=_font(12, bold=True))

    elif style == "concept":
        # 概念图风格 - 中心思想辐射
        _draw_circle_gradient(draw, W//2, H//2, 150, theme["glow"], theme["bg_primary"], 12)
        _draw_particles(draw, W, H, theme, 25)

        # 如果传入了自定义概念项，使用自定义内容
        if concept_items and len(concept_items) >= 3:
            center_text = concept_items[0][0] if len(concept_items[0]) > 0 else "核心"
            outer_items = concept_items[1:] if len(concept_items) >= 4 else concept_items[:3]
        else:
            center_text = "一人组织"
            outer_items = [
                ("AI系统", "四系统驱动"),
                ("超级个体", "一人=一公司"),
                ("认知升维", "从OPC到OPD"),
            ]
            if topic:
                center_text = topic[:6] if len(topic) > 6 else topic
        
        # 中心圆
        ct_len = len(center_text)
        ct_font_size = 22 if ct_len <= 4 else 18
        _draw_circle_gradient(draw, W//2, H//2, 55, theme["accent_light"], theme["bg_primary"], 30)
        draw.ellipse([W//2-40, H//2-40, W//2+40, H//2+40],
                     outline=(*theme["accent"], 100), width=1)
        draw.text((W//2 - ct_len * 7, H//2-10), center_text, fill=(*theme["accent_light"], 240), font=_font(ct_font_size, bold=True))

        # 辐射文字 - 根据实际内容生成
        positions = [
            (W//2, 25),
            (W-10, H//2-20),
            (W//2, H-35),
            (15, H//2-20),
        ]
        for i, ((cx, cy), (item_name, item_desc)) in enumerate(zip(positions, outer_items)):
            draw.line([(W//2, H//2), (cx, cy)], fill=(*theme["accent"], 25), width=1)
            draw.text((cx-50, cy-6), f"{item_name}", fill=(*theme["text_dim"], 200), font=_font(13, bold=True))
            draw.text((cx-40, cy+16), f"{item_desc}", fill=(*theme["text_dim"], 130), font=_font(10))

    elif style == "steps":
        # 步骤图
        _draw_particles(draw, W, H, theme, 10)

        # 如果传入了自定义步骤项，使用自定义内容
        if step_items and len(step_items) >= 2:
            steps = step_items[:3]  # 最多3步
        else:
            steps = [
                ("Step 1", "诊断现状", "梳理四系统薄弱环节"),
                ("Step 2", "AI化薄弱系统", "用AI工具替换人工"),
                ("Step 3", "逐步扩展", "系统化后复制到其他系统"),
            ]
        step_w = (W-60) // 3
        for idx, (step_label, step_title, step_desc) in enumerate(steps):
            sx = 20 + idx * (step_w + 10)
            sy = 50
            # 步骤框
            draw.rounded_rectangle(
                [sx, sy, sx+step_w-10, sy+150],
                radius=12,
                fill=(*theme["bg_secondary"], 200),
                outline=(*theme["accent"], 80),
                width=1
            )
            # 步骤编号
            draw.ellipse([sx+15, sy+15, sx+35, sy+35], fill=(*theme["accent"], 160))
            draw.text((sx+20, sy+18), str(idx+1), fill=(*theme["bg_primary"], 240), font=_font(14, bold=True))
            # 步骤标签
            draw.text((sx+45, sy+18), step_label, fill=(*theme["accent_dim"], 180), font=_font(11))
            # 步骤标题
            draw.text((sx+15, sy+50), step_title, fill=(*theme["accent_light"], 230), font=_font(16, bold=True))
            # 步骤描述
            draw.text((sx+15, sy+80), step_desc, fill=(*theme["text_dim"], 180), font=_font(13))

            # 箭头
            if idx < len(steps) - 1:
                ax, ay = sx+step_w+2, sy+75
                draw.text((ax-2, ay), "→", fill=(*theme["accent"], 100), font=_font(20))

        draw.text((W//2-30, H-22), "三步构建你的 OP", fill=(*theme["text_dim"], 100), font=_font(11))

    else:
        # quote 风格 - 金句卡片
        _draw_circle_gradient(draw, W//2, H//2, 180, theme["glow"], theme["bg_primary"], 8)
        _draw_particles(draw, W, H, theme, 15)

        # 引号
        draw.text((30, 25), "\u201c", fill=(*theme["accent"], 120), font=_font(60))
        draw.text((W-60, H-95), "\u201d", fill=(*theme["accent"], 120), font=_font(60))

        # 金句
        # 优先使用传入的自定义金句文本
        if quote_text:
            quote = quote_text[:60] if len(quote_text) > 60 else quote_text
        else:
            quote = title if len(title) <= 40 else title[:37] + "..."
        lines = _title_to_lines(quote, _font(18), W-120)
        for i, line in enumerate(lines):
            draw.text((40, 70+i*30), line, fill=(*theme["text"], 230), font=_font(18))

        # 底部品牌
        draw.text((40, H-35), f"—— {BRAND_NAME}", fill=(*theme["accent_dim"], 160), font=_font(13))

    # ===== 底部微装饰 =====
    draw.line([(15, H-5), (W-15, H-5)], fill=(*theme["accent"], 8), width=1)

    # ===== 保存 =====
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in title[:20])
    path = OUTPUT_DIR / f"inline_{safe_name}_{style}.png"
    img.convert("RGB").save(path, "PNG", optimize=True)
    print(f"✅ 配图已生成: {path} (样式: {style}, 配色: {theme['name']})")
    return path


def batch_generate(title, topic="", keywords=None):
    """为单篇文章批量生成封面+配图"""
    print(f"\n{'='*50}")
    print(f"📝 正在为文章生成图片: {title}")
    print(f"{'='*50}")

    # 1. 封面图
    cover_path = generate_cover_enhanced(title, topic, keywords)
    cover_size = cover_path.stat().st_size
    print(f"   封面大小: {cover_size/1024:.1f} KB")

    # 2. 配图 - 根据主题选择风格
    style_map = {
        "OPD": ["diagram", "info", "concept"],
        "副业": ["steps", "concept", "quote"],
        "顺道而为": ["concept", "steps", "quote"],
    }
    styles = ["diagram", "info", "concept", "steps"]
    for key, s_list in style_map.items():
        if key in title or key in topic:
            styles = s_list
            break

    inline_paths = []
    for i, style in enumerate(styles[:3]):
        sub_title = f"{title} - 图{i+1}"
        inline_path = generate_inline_image(sub_title, style, topic,
                                             width=640, height=400)
        inline_size = inline_path.stat().st_size
        print(f"   {style}配图: {inline_size/1024:.1f} KB")
        inline_paths.append(inline_path)

    return cover_path, inline_paths


if __name__ == "__main__":
    # 测试运行
    batch_generate("你离副业成功，只差一个不做勇气", "副业", ["副业", "创业"])
    batch_generate("OPC已死，OPD当立", "AI科技", ["AI", "科技"])
    batch_generate("顺道而为的人都有这3个共同点", "认知升级", ["认知升级", "成长"])
