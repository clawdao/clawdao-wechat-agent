#!/usr/bin/env python3
"""
发布两篇精选文章到微信公众号草稿箱：
1. 「减少依赖，是 2026 年最被低估的竞争力」
2. 「SaaS 越买越焦虑？少则得，多则惑」

使用 deluxe 设计引擎生成的高精度封面和插图
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.publisher import WeChatPublisher

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

def publish_article(article_file, cover_name, article_title):
    """发布单篇文章"""
    # 读取文章内容
    md_path = os.path.join(OUTPUT_DIR, article_file)
    if not os.path.exists(md_path):
        print(f"❌ 文章文件不存在: {md_path}")
        return False
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 封面图路径
    cover_path = os.path.join(OUTPUT_DIR, cover_name)
    if not os.path.exists(cover_path):
        print(f"⚠️  封面图不存在（将使用默认封面）: {cover_path}")
        cover_path = None
    
    print(f"\n{'='*50}")
    print(f"📝 发布文章: {article_title}")
    print(f"   📄 文件: {md_path}")
    print(f"   🖼️  封面: {cover_path or '默认'}")
    print(f"{'='*50}")
    
    # 发布
    publisher = WeChatPublisher()
    success = publisher.save_as_draft(
        title=article_title,
        content=content,
        cover_image_path=cover_path
    )
    return success


if __name__ == "__main__":
    print(f"\n{'='*55}")
    print("🚀 觉知岛 · 公众号文章批量发布")
    print(f"{'='*55}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"Python: {sys.executable}")
    print(f"{'='*55}\n")
    
    results = []
    
    # ===== 文章1：「减少依赖，是 2026 年最被低估的竞争力」 =====
    r1 = publish_article(
        article_file="article_减少依赖_2026.md",
        cover_name="觉知岛_减少依赖_文章封面_900x500.png",
        article_title="减少依赖，是 2026 年最被低估的竞争力"
    )
    results.append(("减少依赖，是 2026 年最被低估的竞争力", r1))
    
    # ===== 文章2：「SaaS 越买越焦虑？少则得，多则惑」 =====
    r2 = publish_article(
        article_file="article_SaaS越买越焦虑.md",
        cover_name="觉知岛_SaaS越买越焦虑_文章封面_900x500.png",
        article_title="SaaS 越买越焦虑？少则得，多则惑"
    )
    results.append(("SaaS 越买越焦虑？少则得，多则惑", r2))
    
    # 汇总
    print(f"\n{'='*55}")
    print("📊 发布汇总")
    print(f"{'='*55}")
    for title, ok in results:
        status = "✅ 成功" if ok else "❌ 失败"
        print(f"  {status}: {title}")
    print(f"{'='*55}")
