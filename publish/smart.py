#!/usr/bin/env python3
"""
智能发布脚本——使用 Seedream AI 根据文章内容生成封面和配图
品牌头图自动从 Obsidian 知识库同步

用法：
    python3 publish_smart.py "选题" --style 风格
    python3 publish_smart.py "选题" --from-article 文章文件路径
    python3 publish_smart.py "选题" --from-outline 大纲文件路径
    python3 publish_smart.py "选题" --no-publish
"""
import re, sys, os, argparse, shutil
from pathlib import Path
from core.article import generate_article, extract_title
from covers.base import generate_cover  # 回退方案
from core.publisher import WeChatPublisher

BASE = Path(__file__).parent
OUT = BASE / 'output'

# Obsidian 知识库路径
OBSIDIAN_KNOWLEDGE_BASE = Path('/Users/imfly/Documents/13-运营知识库/公众号自动发布智能体')
OBSIDIAN_BRAND_HEADER = OBSIDIAN_KNOWLEDGE_BASE / 'output' / 'brand_header.png'


def sync_brand_header():
    """从 Obsidian 知识库同步品牌头图到项目目录"""
    if OBSIDIAN_BRAND_HEADER.exists():
        dest = OUT / 'brand_header.png'
        shutil.copy2(str(OBSIDIAN_BRAND_HEADER), str(dest))
        return True
    return False


def extract_keywords(topic: str) -> list:
    """从选题中提取关键词"""
    # 主题 → 关键词映射
    tag_map = {
        "一人": ["一人组织", "AI转型", "四系统", "超级个体", "组织革命"],
        "组织": ["一人组织", "OPD", "四系统", "AI驱动", "组织效率"],
        "AI": ["AI", "人工智能", "科技趋势", "大模型", "自动化"],
        "认知": ["认知升级", "成长", "思维", "认知科学", "元认知"],
        "创业": ["创业", "副业", "商业模式", "创始人", "精益创业"],
        "算力": ["GPU算力", "AI泡沫", "CoreWeave", "算力租赁", "H100"],
        "副业": ["副业", "创业", "自由职业", "一人企业", "收入多元化"],
        "系统": ["OPD", "四系统", "管理系统", "知识系统", "产品系统"],
    }
    for key, tags in tag_map.items():
        if key in topic:
            return tags
    return [topic[:8]]


def load_article(filepath: str) -> str:
    """加载文章文件"""
    path = Path(filepath)
    if not path.exists():
        print(f'❌ 文章文件不存在: {path}')
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def insert_inline_images(article: str, inline_paths: list, alt_texts: list) -> str:
    """在正文中插入配图引用（先清理旧引用，再插入新引用）"""
    # 先清除所有已有图片引用
    import re as _re
    article = _re.sub(r'\n?!\[.+?\]\(\./.+?\.png\)\n?', '\n', article)
    article = _re.sub(r'\n{3,}', '\n\n', article)
    lines = article.split('\n')
    inserted = 0
    for idx, (ip, alt) in enumerate(zip(inline_paths, alt_texts)):
        mid = len(lines) // 2
        pos = mid + idx * (len(lines) // 5)
        placed = False
        for j in range(pos, min(pos+5, len(lines))):
            if lines[j].strip() == '' and j+1 < len(lines) and lines[j+1].strip() != '':
                lines.insert(j+1, f'\n![{alt}](./{ip.name})\n')
                inserted += 1
                placed = True
                break
        if not placed:
            lines.append(f'\n![{alt}](./{ip.name})\n')
            inserted += 1
    return '\n'.join(lines), inserted


def generate_images_with_seedream(title: str, topic: str, keywords: list,
                                   step_items: list, concept_items: list,
                                   quote_text: str):
    """使用 Seedream 根据文章内容生成封面和配图"""
    from config import get_seedream_config
    from seedream_generator import SeedreamGenerator

    scfg = get_seedream_config()
    if not scfg.get("enabled", False):
        print('  ⚠️ Seedream 未启用，使用 PIL 方案')
        return None, []

    sg = SeedreamGenerator(scfg)
    if not sg.enabled:
        print('  ⚠️ Seedream 不可用，使用 PIL 方案')
        return None, []

    # 封面
    print('  🖼️ 生成封面（Seedream AI）...')
    cover_path = sg.generate_cover(title, topic=topic, keywords=keywords)

    # 品牌头图（如不存在则生成）
    brand_path = OUT / 'brand_header.png'
    if not brand_path.exists():
        print('  🏷️ 生成品牌头图...')
        sg.generate_brand_header()

    # 配图
    inline_paths = []
    style_list = ["steps", "concept", "quote"]
    style_names = ["步骤图", "概念图", "金句图"]
    custom_contents = [step_items, concept_items, quote_text]

    for i, style in enumerate(style_list):
        content_text = custom_contents[i]
        # 用实际内容作为配图标题，让 Seedream 生成相关背景
        sub_title = str(content_text[0][1] if isinstance(content_text, list) and len(content_text) > 0 else content_text) if isinstance(content_text, (list, str)) else topic
        sub_title = sub_title[:30] if len(str(sub_title)) > 30 else str(sub_title) if sub_title else topic[:30]
        
        print(f'  🎨 生成配图 {i+1}/{len(style_list)} ({style_names[i]})...')
        ip = sg.generate_inline_image(
            sub_title, style, topic=topic,
            width=640, height=400
        )
        inline_paths.append(ip)

    return cover_path, inline_paths


def generate_images_pil(title: str, topic: str,
                         step_items: list, concept_items: list,
                         quote_text: str):
    """PIL 回退方案生成封面和配图"""
    from cover_generator import generate_cover
    from image_generator_enhanced import generate_inline_image
    
    print('  🖼️ 生成封面（PIL）...')
    cover_path = generate_cover(title, topic)
    
    inline_paths = []
    
    # 步骤图
    if step_items and len(step_items) >= 2:
        step_text = " → ".join([s[1] for s in step_items])
    else:
        step_text = topic
    ip1 = generate_inline_image(step_text, 'steps', topic, step_items=step_items)
    inline_paths.append(ip1)
    
    # 概念图
    center_text = topic[:6] if len(topic) > 6 else topic
    ip2 = generate_inline_image(center_text, 'concept', topic, concept_items=concept_items)
    inline_paths.append(ip2)
    
    # 金句图
    qt = quote_text or "好文"
    ip3 = generate_inline_image(qt[:30], 'quote', topic, quote_text=qt)
    inline_paths.append(ip3)
    
    return cover_path, inline_paths


def main():
    parser = argparse.ArgumentParser(description='智能发布 - 文章生成+配图+发布')
    parser.add_argument('topic', nargs='?', default='', help='选题')
    parser.add_argument('--style', default='轻松专业', help='文章风格')
    parser.add_argument('--from-article', help='使用已有的文章文件（不重新生成）')
    parser.add_argument('--from-outline', help='从文案大纲文件生成')
    parser.add_argument('--no-publish', action='store_true', help='只生成不发布')
    args = parser.parse_args()

    # 获取文章内容
    if args.from_article:
        print(f'📄 加载已有文章: {args.from_article}')
        article = load_article(args.from_article)
        topic = args.topic or extract_title(article) or "文章"
    elif args.from_outline:
        outline_path = Path(args.from_outline)
        if not outline_path.exists():
            print(f'❌ 大纲文件不存在: {outline_path}')
            sys.exit(1)
        with open(outline_path, 'r', encoding='utf-8') as f:
            outline = f.read()
        title_match = re.search(r'^标题[:：]\s*(.+)', outline, re.M)
        topic = title_match.group(1).strip() if title_match else args.topic
        print(f'📄 从大纲读取: {outline_path.name}')
        article = generate_article(topic, args.style)
    else:
        topic = args.topic
        if not topic:
            print('❌ 请提供选题、文章文件或大纲文件')
            sys.exit(1)
        article = generate_article(topic, args.style)

    print(f'📌 选题: {topic}')
    print(f'📝 字数: {len(article)}字')

    # 提取文章中的真实内容用于配图
    # 步骤
    steps = []
    for line in article.split('\n'):
        line = line.strip()
        if re.match(r'^(\d+[.、]|第[一二三四五六七八九十]+步)', line):
            text = re.sub(r'^(\d+[.、]|第[一二三四五六七八九十]+步)[：:]?\s*', '', line)
            if 4 < len(text) < 25:
                steps.append(text)
    if len(steps) < 2:
        sections = re.findall(r'##\s+\S.+?(?:\n|$)', article)
        for s in sections[:3]:
            title_t = s.replace('##', '').strip().rstrip('：:）)')
            if 4 < len(title_t) < 20:
                steps.append(title_t)
    if len(steps) < 2:
        first_para = ''
        for para in article.split('\n\n'):
            if len(para) > 30 and not para.startswith('#') and not para.startswith('>'):
                first_para = para[:200]
                break
        entities = re.findall(r'\*\*(.+?)\*\*', first_para)
        for e in entities[:3]:
            if 2 < len(e) < 15: steps.append(e)
    step_items = [(f"①", s, "") for i, s in enumerate(steps[:3])]

    # 概念
    concepts = []
    seen = set()
    bold_words = re.findall(r'\*\*(.+?)\*\*', article)
    for w in bold_words:
        w = w.strip()
        if 2 < len(w) < 12 and w not in seen:
            seen.add(w); concepts.append(w)
    if len(concepts) < 3:
        first_para = ''
        for para in article.split('\n\n'):
            if len(para) > 30 and not para.startswith('#') and not para.startswith('>'):
                first_para = para[:300]; break
        nouns = re.findall(r'[一-龥]{2,6}', first_para)
        for n in nouns[:6]:
            if n not in seen and len(n) >= 2:
                seen.add(n); concepts.append(n)
    center = concepts[0] if concepts else topic[:6]
    outer = concepts[1:4] if len(concepts) >= 4 else concepts[:3]
    concept_items = [(center, "")] + [(c, "") for c in outer]

    # 金句
    quotes = []
    for line in article.split('\n'):
        line = line.strip()
        if line.startswith('> ') and len(line) > 5:
            text = line[2:].strip().strip('"').strip('"').strip('「').strip('」')
            if 10 < len(text) < 60: quotes.append(text)
    quote_text = quotes[0] if quotes else ""

    keywords = extract_keywords(topic)

    # 同步品牌头图
    print('\n🏷️ 同步品牌头图...')
    sync_brand_header()

    # 使用 Seedream 生成封面和配图
    print('\n🎨 生成图文素材（基于文章内容）...')
    
    cover_path, inline_paths = generate_images_with_seedream(
        topic, topic, keywords, step_items, concept_items, quote_text
    )

    # 如果 Seedream 不可用，回退 PIL
    if cover_path is None:
        cover_path, inline_paths = generate_images_pil(
            topic, topic, step_items, concept_items, quote_text
        )

    # 配图 alt 文字（用实际文章内容，不用分类标签）
    alt_texts = []
    if step_items:
        alt_texts.append(" → ".join([s[1] for s in step_items])[:30])
    else:
        alt_texts.append(topic[:20])
    if concept_items and len(concept_items) > 1:
        alt_texts.append(f"{concept_items[0][0]} {' '.join([c[0] for c in concept_items[1:]])}"[:30])
    else:
        alt_texts.append(topic[:20])
    alt_texts.append(quote_text[:30] if quote_text else topic[:20])

    # 插入配图到正文
    print('\n📝 插入配图到正文...')
    article_with_images, inserted = insert_inline_images(article, inline_paths, alt_texts)

    # 保存
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in topic[:15])
    raw_path = OUT / f'article_{safe_name}.md'
    with open(raw_path, 'w', encoding='utf-8') as f:
        f.write(article_with_images)
    print(f'💾 文章保存: {raw_path}')

    # 发布
    if not args.no_publish:
        print('\n📤 发布到微信草稿箱...')
        publisher = WeChatPublisher()
        success = publisher.save_as_draft(
            title=topic,
            content=article_with_images,
            cover_image_path=str(cover_path),
        )
        if success:
            print('\n🎉 发布成功！')
            print(f'   标题：{topic}')
            print(f'   头图：知识库 brand_header.png ✓')
            print(f'   封面：Seedream AI 按主题生成 ✓')
            print(f'   配图：{inserted}张（Seedream AI 按内容生成）✓')
        else:
            print('\n⚠️ 发布失败')
    else:
        print('\n✅ 生成完成（--no-publish 模式）')


if __name__ == '__main__':
    main()
