#!/usr/bin/env python3
"""
公众号文章自动生成器 - 精排版版（增强图片版）
一键生成：文章 + 精美封面图 + 内部配图 + 发布到微信草稿箱

用法：
    python3 main.py "你的选题" [--style 风格] [--no-publish] [--no-cover]
"""

import re
import sys
import argparse
from pathlib import Path
from article_generator import generate_article, extract_title
from image_generator_enhanced import generate_cover_enhanced, generate_inline_image
from wechat_publisher import WeChatPublisher


def clean_title(title: str) -> str:
    """清理特殊字符，保留长度（微信支持64字）"""
    for ch in ['"', '"', "'", "'"]:
        title = title.replace(ch, '')
    return title.strip()


def get_topic_tags(topic: str) -> list:
    """GEO增强版：根据选题生成关键词标签（实体密度更高的标签）"""
    tag_map = {
        "副业": ["副业", "创业", "自由职业", "一人企业", "收入多元化"],
        "创业": ["创业", "副业", "商业模式", "创始人", "精益创业"],
        "AI": ["AI", "人工智能", "科技趋势", "大模型", "自动化"],
        "科技": ["科技", "AI", "效率", "数字化", "数字化转型"],
        "认知": ["认知升级", "成长", "思维", "认知科学", "元认知"],
        "成长": ["成长", "认知升级", "效率", "个人发展", "自我管理"],
        "OPD": ["OPD", "组织效率", "认知升级", "一人组织", "AI驱动"],
        "效率": ["效率", "工具", "方法论", "自动化", "工作流"],
        "管理": ["管理", "领导力", "组织", "团队", "CEO"],
        "道德经": ["道德经", "老子", "东方智慧", "无为而治", "管理哲学"],
        "无为": ["无为而治", "道德经", "老子", "管理哲学", "领导力"],
        "区块链": ["区块链", "Web3", "DAO", "去中心化", "智能合约"],
        "IP": ["IP", "个人品牌", "内容创业", "知识付费", "影响力"],
    }
    tags = []
    for key, val in tag_map.items():
        if key in topic:
            tags.extend(val)
    result = list(set(tags))
    return result if result else ["认知升级", "效率", "AI时代"]


def extract_article_content(article: str) -> tuple:
    """从文章提取步骤、概念、金句用于配图"""
    # 步骤
    steps = []
    for line in article.split("\n"):
        line = line.strip()
        if re.match(r"^(\d+[.、]|第[一二三四五六七八九十]+步)", line):
            text = re.sub(r"^(\d+[.、]|第[一二三四五六七八九十]+步)[：:]?\s*", "", line)
            if 4 < len(text) < 25:
                steps.append(text)
    if len(steps) < 2:
        sections = re.findall(r"##\s+\S.+?(?:\n|$)", article)
        for s in sections[:3]:
            t = s.replace("##", "").strip().rstrip("：:）)")
            if 4 < len(t) < 20:
                steps.append(t)

    # 概念（加粗关键词）
    concepts = []
    seen = set()
    bold_words = re.findall(r"\*\*(.+?)\*\*", article)
    for w in bold_words:
        w = w.strip()
        if 2 < len(w) < 12 and w not in seen:
            seen.add(w)
            concepts.append(w)

    # 金句
    quotes = []
    for line in article.split("\n"):
        line = line.strip()
        if line.startswith("> ") and len(line) > 5:
            text = line[2:].strip().strip('"').strip("'").strip("「").strip("」")
            if 10 < len(text) < 60:
                quotes.append(text)

    return steps, concepts, quotes


def insert_images(article: str, inline_paths: list) -> str:
    """将配图引用插入文章（注意：正文不放封面图）"""
    # 先清除所有已有图片引用
    article = re.sub(r"\n?!\[.+?\]\(\./.+?\.png\)\n?", "\n", article)
    article = re.sub(r"\n{3,}", "\n\n", article)
    lines = article.split("\n")

    for idx, ip in enumerate(inline_paths[:3]):
        inline_rel = ip.name
        # 使用有意义的内容作为alt
        alt_texts = ["步骤流程示意", "核心概念解析", "金句观点"]
        inline_md = f"\n![{alt_texts[idx] if idx < len(alt_texts) else '配图'}](./{inline_rel})\n"

        # 在文章后半段找插入点
        mid = len(lines) // 2
        insert_after = mid + idx * (len(lines) // 6)
        if insert_after >= len(lines):
            insert_after = len(lines) - 2
        for j in range(insert_after, min(insert_after + 5, len(lines))):
            if lines[j].strip() == "":
                lines.insert(j, inline_md)
                break
        else:
            lines.insert(insert_after, inline_md)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="公众号文章自动生成器 - 一键生成文章+精美图片+发布草稿"
    )
    parser.add_argument("topic", type=str, help="文章选题")
    parser.add_argument("--style", type=str, default="轻松专业",
                        help="文章风格（轻松专业/深度分析/暖心故事/实用教程）")
    parser.add_argument("--no-publish", action="store_true",
                        help="只生成文章和图片，不发布到公众号")
    parser.add_argument("--no-cover", action="store_true",
                        help="只生成文章，不生成封面和配图")
    parser.add_argument("--no-images", action="store_true",
                        help="不生成正文配图")
    parser.add_argument("--use-seedream", action="store_true",
                        help="强制使用 Seedream 生成图片")
    parser.add_argument("--publish-only", action="store_true",
                        help="仅发布已有文章（需配合 --article-file）")
    parser.add_argument("--article-file", type=str,
                        help="指定已有文章文件路径")
    parser.add_argument("--cover-file", type=str,
                        help="指定已有封面文件路径")

    args = parser.parse_args()
    topic = args.topic
    article_path = None

    if args.publish_only:
        if not args.article_file:
            print("❌ --publish-only 需要 --article-file")
            sys.exit(1)
        article_path = Path(args.article_file)
        if not article_path.exists():
            print(f"❌ 文章文件不存在: {article_path}")
            sys.exit(1)
        with open(article_path, "r", encoding="utf-8") as f:
            article = f.read()
        print(f"📄 从文件读取文章: {article_path}")
    else:
        print(f"\n🤖 正在生成文章... 选题: {topic}")
        article = generate_article(topic, args.style)
        print(f"✅ 文章生成完毕，字数: {len(article)}")

    title = clean_title(extract_title(article) if article else topic)
    print(f"📌 标题: {title}")

    cover_path = None
    if not args.no_cover:
        print("\n🎨 生成图文素材...")

        tags = get_topic_tags(args.topic or topic)

        # 尝试使用 Seedream
        inline_paths = []
        try:
            from config import get_seedream_config
            scfg = get_seedream_config()
            use_seedream = args.use_seedream or scfg.get("enabled", False)
            if use_seedream:
                print("  🔮 使用 Seedream AI 生成独特图像...")
                from seedream_generator import SeedreamGenerator
                sg = SeedreamGenerator(scfg)
                if sg.enabled:
                    # 1. 生成封面图
                    print("  🖼️ 生成封面图...")
                    cover_path = sg.generate_cover(title, args.topic, tags)

                    # 2. 同步品牌头图（从知识库）
                    from publish_smart import sync_brand_header
                    sync_brand_header()

                    # 3. 从文章提取实际内容生成配图
                    steps, concepts, quotes = extract_article_content(article)
                    style_list = ["steps", "concept", "quote"]

                    for i, style in enumerate(style_list):
                        if style == "steps" and steps:
                            sub_title = " → ".join(steps[:3])[:30]
                        elif style == "concept":
                            # 组合概念词
                            if concepts:
                                sub_title = " · ".join(concepts[:3])[:30]
                            else:
                                sub_title = f"{title[:12]}概念解析"
                        else:
                            sub_title = quotes[0][:30] if quotes else f"{title[:12]}核心观点"
                        if not args.no_images:
                            print(f"  🎨 生成配图 {i+1}/3...")
                            ip = sg.generate_inline_image(sub_title or f"{topic[:15]}-{style}", style, args.topic,
                                                           width=640, height=400)
                            inline_paths.append(ip)
        except Exception as e:
            print(f"  ⚠️ 生成失败: {e}")

        # 如果 Seedream 不可用或无配图生成成功，回退 PIL
        if cover_path is None and not args.no_cover:
            print("  🖼️ 使用 PIL 生成封面...")
            cover_path = generate_cover_enhanced(title, args.topic, tags)

        if not inline_paths and not args.no_images and not args.no_cover:
            print("  🎨 使用 PIL 生成配图...")
            style_list = ["steps", "concept", "quote"]
            steps, concepts, quotes = extract_article_content(article)
            for i, style in enumerate(style_list):
                if style == "steps" and steps:
                    sub_title = " → ".join(steps[:3])[:30]
                elif style == "concept" and concepts:
                    sub_title = " · ".join(concepts[:3])[:30]
                elif style == "quote" and quotes:
                    sub_title = quotes[0][:30]
                else:
                    sub_title = f"{title} - 图{i+1}"
                ip = generate_inline_image(sub_title, style, args.topic, width=640, height=400)
                inline_paths.append(ip)

        if not args.no_images and inline_paths:
            article = insert_images(article, inline_paths)
            print(f"✅ 已向文章中插入 {len(inline_paths)} 张配图")

    # 保存文章
    if not article_path:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic[:15])
        article_path = Path(__file__).parent / "output" / f"article_{safe_name}.md"
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(article)
    print(f"💾 文章已保存: {article_path}")

    if not args.no_publish:
        print("\n📤 正在发布到公众号草稿箱...")
        publisher = WeChatPublisher()
        success = publisher.save_as_draft(
            title=title,
            content=article,
            cover_image_path=str(cover_path) if cover_path else None,
        )
        if success:
            print("\n🎉 全部完成！文章已保存到公众号草稿箱。")
            print(f"   标题：{title}")
            print(f"   字数：{len(title)}字")
            print(f"   作者：顺道大叔")
            print(f"   封面：1:1安全区 ✓ | 正文不放封面 ✓")
            print(f"   品牌头图：知识库同步 ✓")
            print(f"   配图：{len(inline_paths) if not args.no_images else 0}张 | alt用实际内容 ✓")
            print(f"   🔍 GEO优化：JSON-LD + 语义HTML + 实体关键词")
        else:
            print("\n⚠️  文章和图片已生成，但发布到公众号失败。")
            print("   请检查 config.json 中的微信配置是否正确。")
    else:
        print("\n✅ 生成完成！（--no-publish 模式，未发布到公众号）")


if __name__ == "__main__":
    main()
