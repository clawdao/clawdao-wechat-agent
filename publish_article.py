#!/usr/bin/env python3
"""
发布文章到微信草稿箱
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wechat_publisher import WeChatPublisher
from pathlib import Path

ART_PATH = Path(__file__).parent / "output" / "05-从用软件到长软件_配图版.md"
COV_PATH = Path(__file__).parent / "output" / "觉知岛_文章封面_900x500.png"

def main():
    print("=" * 55)
    print("  觉知岛 · 微信发布")
    print("=" * 55)
    
    if not ART_PATH.exists():
        print(f"  ❌ 文章不存在: {ART_PATH}")
        sys.exit(1)
    
    content = ART_PATH.read_text(encoding="utf-8")
    title_line = content.split("\n")[0]
    title = title_line.lstrip("# ").strip()
    
    print(f"\n  标题: {title}")
    print(f"  长度: {len(content)} 字符")
    
    cover_path = str(COV_PATH) if COV_PATH.exists() else None
    if cover_path:
        print(f"  封面: {COV_PATH.name} ({COV_PATH.stat().st_size//1024} KB)")
    else:
        print("  ⚠️ 封面图不存在，跳过封面设置")
    
    print(f"\n{'─'*50}")
    print("  正在发布到微信草稿箱...")
    print(f"{'─'*50}")
    
    publisher = WeChatPublisher()
    success = publisher.save_as_draft(title, content, cover_path)
    
    if success:
        print(f"\n{'='*55}")
        print("  ✅ 文章已成功发布到微信草稿箱！")
        print(f"{'='*55}")
        print(f"\n  请登录公众号后台:")
        print(f"  草稿箱 → 找到最新草稿 → 预览 → 发布")
    else:
        print(f"\n{'='*55}")
        print("  ❌ 发布失败，请检查错误日志")
        print(f"{'='*55}")

if __name__ == "__main__":
    main()
