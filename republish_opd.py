"""重新发布三篇OPD文章 - 精排版"""
import os, sys, json, re, time
sys.path.insert(0, '.')
from wechat_publisher import WeChatPublisher
from cover_generator import generate_cover
from article_generator import extract_title

ARTICLES = [
    {"file": "output/article_opd_01.md"},
    {"file": "output/article_opd_02.md"},
    {"file": "output/article_opd_03.md"},
]

def embed_image_marker(md_text, topic, idx):
    """在文章中间插入图片标记 — 在Lens段后放一张"""
    lines = md_text.split("\n")
    # 找第一个 --- 或 ## 后面的位置插入
    insert_pos = None
    section_count = 0
    for i, line in enumerate(lines):
        if line.startswith("## ") or line.startswith("---"):
            section_count += 1
            if section_count == 3:  # 第二个小标题/分隔线后插入
                insert_pos = i + 1
                break

    if insert_pos is None:
        insert_pos = len(lines) // 2

    # 生成图片路径
    out_dir = os.path.join(os.path.dirname(__file__), 'output')
    img_path = os.path.join(out_dir, f"inline_opd_{idx}.png")
    
    # 生成文中插图
    from PIL import Image, ImageDraw, ImageFont
    from pathlib import Path
    
    W, H = 900, 400
    img = Image.new("RGBA", (W, H), (8, 10, 18))
    draw = ImageDraw.Draw(img)
    
    # 渐变
    accent = (200, 170, 60)
    for y in range(H):
        r = int(8 + (16 - 8) * y / H)
        g = int(10 + (18 - 10) * y / H)
        b = int(18 + (28 - 18) * y / H)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    
    # 装饰
    draw.ellipse([W//2-120, H//2-80, W//2-40, H//2], outline=(*accent, 20), width=1)
    draw.ellipse([W//2+40, H//2-80, W//2+120, H//2], outline=(*accent, 20), width=1)
    draw.line([(60, H-60), (W-60, H-60)], fill=(*accent, 15), width=1)
    
    # 文字
    font_paths = ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc"]
    ft = None
    for p in font_paths:
        if Path(p).exists():
            ft = ImageFont.truetype(p, 24)
            break
    
    if ft:
        draw.text((W//2-80, H//2-30), "◆ 觉知岛", fill=(*accent, 160), font=ft)
        ft2 = ImageFont.truetype(font_paths[0] if Path(font_paths[0]).exists() else font_paths[1], 18)
        draw.text((W//2-100, H//2+20), "一人组织 · 顺道而为", fill=(*accent, 90), font=ft2)
        ft3 = ImageFont.truetype(font_paths[0] if Path(font_paths[0]).exists() else font_paths[1], 14)
        safe_topic = topic[:30]
        draw.text((W//2-120, H-50), f"{safe_topic}", fill=(*accent, 50), font=ft3)
    
    import random
    random.seed(hash(topic))
    for _ in range(25):
        x = random.randint(30, W-30)
        y = random.randint(20, H-20)
        draw.ellipse([x-1, y-1, x+1, y+1], fill=(*accent, random.randint(5, 20)))
    
    img.convert("RGB").save(img_path, "PNG", optimize=True)
    
    # 在文章中插入图片标记
    img_marker = f"\n![插图]({img_path})\n"
    lines.insert(insert_pos, img_marker)
    
    return "\n".join(lines), img_path

publisher = WeChatPublisher()

for idx, art in enumerate(ARTICLES, 1):
    print(f"\n{'='*50}")
    print(f"📤 重新发布第{idx}篇...")
    
    with open(art["file"], 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    # 提取标题
    title = extract_title(md_text) or f"OPD系列第{idx}篇"
    for ch in ['"', '"', "'", "'"]:
        title = title.replace(ch, '')
    
    print(f"  标题：{title} ({len(title)}字)")
    
    # 生成文中插图
    md_with_img, img_path = embed_image_marker(md_text, title, idx)
    print(f"  文中插图已生成")
    
    # 生成封面
    cover = generate_cover(title[:20], f"OPD系列第{idx}篇")
    print(f"  封面已生成")
    
    # 发布
    print(f"  正在发布...")
    success = publisher.save_as_draft(
        title=title,
        content=md_with_img,
        cover_image_path=str(cover),
    )
    
    if success:
        print(f"  ✅ 第{idx}篇发布成功！（作者：顺道大叔，标题{len(title)}字）")
    else:
        print(f"  ⚠️ 第{idx}篇发布失败")
    
    time.sleep(2)  # 避免频率限制

print(f"\n{'='*50}")
print("🎉 三篇文章重新发布完成！")
print("  作者：顺道大叔")
print("  标题：支持64字")
print("  排版：精排版（金色渐变标题+彩色小标题+金句引用+文中插图）")
