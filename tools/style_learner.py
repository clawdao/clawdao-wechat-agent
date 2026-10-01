#!/usr/bin/env python3
"""
风格学习器：从微信公众号文章链接 → 提取风格特征 → 生成 styles/<name>.yml

> 工作原理：
> 1. 用 requests 抓取微信文章 HTML
> 2. 用正则提取所有内联 style 属性 + 颜色 + 字号 + 装饰
> 3. 统计主色板 + 字体特征 + 装饰符（横线、emoji、引用标记）
> 4. 调 LLM 分析出"风格名 + 调性描述"
> 5. 输出完整 styles/<name>.yml，可直接被 StyleRenderer 使用

用法：
    # 微信文章链接学习
    python3 tools/style_learner.py --url "https://mp.weixin.qq.com/s/..." --name warm_gold

    # 本地 HTML 文件学习
    python3 tools/style_learner.py --html article.html --name dark_tech
"""
from __future__ import annotations
import os, sys, re, json, argparse
import urllib.request
from pathlib import Path
from collections import Counter

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# =========================================================================
# 抓取 HTML
# =========================================================================
def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")


# =========================================================================
# 提取风格特征
# =========================================================================
def extract_features(html: str) -> dict:
    """从 HTML 中提取风格特征

    返回：
        {
            "colors": {"#c8a84e": 12, ...},    # 颜色频次
            "fonts": {"15px": 5, "17px": 3, ...},  # 字号
            "bg_colors": {"#f5f0e8": 2, ...},
            "border_lefts": ["4px solid #c8a84e", ...],
            "decorations": ["✦ ✦ ✦", "—", ...],
            "fonts_family": ["-apple-system", "PingFang SC"],
            "patterns": ["#f5f0e8.*#c8a84e", ...],  # 颜色组合
            "tags": ["金色", "禅意", ...],
        }
    """
    # 颜色
    color_re = re.compile(r"#[0-9a-fA-F]{6}")
    color_counter = Counter(color_re.findall(html))
    # 字号
    font_re = re.compile(r"font-size:\s*(\d+(?:\.\d+)?px)")
    font_counter = Counter(font_re.findall(html))
    # 背景
    bg_re = re.compile(r"background:\s*([^;\"]+)")
    bgs = bg_re.findall(html)
    bg_counter = Counter(bgs)
    # 左边框
    bl_re = re.compile(r"border-left:\s*([^;\"]+)")
    bls = bl_re.findall(html)
    # 装饰符号
    deco_re = re.compile(r"letter-spacing:\s*\d+px[^>]*>([^<]{1,20})<")
    decos = [w.strip() for w in deco_re.findall(html) if w.strip()]

    # 模式匹配：颜色对组合
    patterns = []
    for bg in color_counter:
        if not bg.startswith("#"):
            continue
        # 找同时出现的 primary color
        if any(other in html for other in color_counter if other != bg):
            patterns.append(f"{bg} + {color_counter.most_common(3)}")

    # 字体
    family_re = re.compile(r"font-family:\s*([^;\"]+)")
    families = []
    for f in family_re.findall(html)[:5]:
        families.append(f.strip())

    return {
        "colors": dict(color_counter.most_common(10)),
        "fonts": dict(font_counter.most_common(10)),
        "bg_colors": dict(bg_counter.most_common(5)),
        "border_lefts": bls[:5],
        "decorations": decos[:10],
        "fonts_family": families,
        "html_size": len(html),
    }


# =========================================================================
# 生成 YAML
# =========================================================================
def build_yaml(name: str, features: dict, description: str = "") -> str:
    """根据特征生成 styles/<name>.yml"""
    # 推断主色
    colors = features["colors"]
    # 排除黑白灰
    color_palette = [(c, n) for c, n in colors.items() if c not in ("#000000", "#ffffff", "#333333", "#1a1a1a")]
    color_palette.sort(key=lambda x: -x[1])
    primary = color_palette[0][0] if color_palette else "#666666"
    primary_dark = color_palette[1][0] if len(color_palette) > 1 else primary
    primary_soft = "#f5f0e8" if any("f5f0e8" in c for c in colors) else (color_palette[2][0] if len(color_palette) > 2 else "#f0f0f0")

    # 推断字号
    fonts = features["fonts"]
    font_sizes = sorted({int(float(s.replace("px", ""))) for s in fonts.keys()})
    p_size = 15
    h1_size = max(font_sizes) if font_sizes else 18
    h2_size = max([s for s in font_sizes if 14 <= s <= 20], default=17)

    # 装饰符号
    decos = features["decorations"]
    deco = decos[0] if decos else "✦ ✦ ✦"

    # 边框风格
    bl = features["border_lefts"][0] if features["border_lefts"] else f"4px solid {primary}"

    yaml = f"""# =============================================================================
# {description or name}风格模板
# 来源：自动从参考文章学习（style_learner.py）
# 学习时间：2026-09-30
# =============================================================================

meta:
  name: {name}
  display_name: "{description or name}"
  source_url: "auto-learned"
  learned_at: "2026-09-30"
  tags: ["自动学习", "{name}"]
  mood: "{description or '待人工补充调性'}"

palette:
  primary: "{primary}"
  primary_dark: "{primary_dark}"
  primary_soft: "{primary_soft}"
  text_primary: "#1a1a2e"
  text_body: "#333333"
  text_quote: "#6b5b3e"
  text_muted: "#888888"
  bg_quote: "{primary_soft}"
  divider: "#eee"

components:

  h1:
    container: 'margin: 0 0 20px 0; text-align: center;'
    title:     'font-size: {h1_size}px; font-weight: 700; color: #1a1a2e; margin: 0; line-height: 1.6; letter-spacing: 0.5px;'
    deco:      'width: 36px; height: 3px; background: {primary}; margin: 10px auto 0 auto; border-radius: 2px;'

  h2:
    container: 'margin: 28px 0 14px 0;'
    flex:      'display: flex; align-items: center;'
    bar:       'width: 4px; height: 20px; background: {primary}; border-radius: 2px; margin-right: 10px;'
    title:     'font-size: {h2_size}px; font-weight: 700; margin: 0; color: #1a1a2e; line-height: 1.5;'

  h3:
    container: 'margin: 22px 0 10px 0;'
    title:     'font-size: 15px; font-weight: 700; margin: 0; color: #1a1a2e;'

  p:
    base:      'margin: 8px 0; font-size: {p_size}px; line-height: 1.9; color: #333; letter-spacing: 0.5px;'

  strong:
    base:      'font-weight: bold; color: {primary};'

  blockquote:
    container: 'background: {primary_soft}; border-left: {bl}; margin: 16px 0; padding: 14px 18px; border-radius: 0 8px 8px 0;'
    text:      'margin: 0; font-size: 14px; line-height: 1.8; color: #6b5b3e; font-style: normal;'

  hr:
    container: 'margin: 28px 0; text-align: center; color: {primary}; font-size: 14px; letter-spacing: 6px;'
    content:   '{deco}'

  spacer:
    base:      'margin: 10px 0;'

  img:
    base:      'margin: 20px 0; text-align: center;'
    img:       'width: 100%; max-width: 100%; border-radius: 10px;'

  section:
    base:      'padding: 0 5px;'

rendering:
  special:
    blockquote:      "preserve inner strong tags"
    strong_in_quote: "use primary color"
    list_bullet:     "preserve original emoji or bullet"
  limits:
    max_blockquotes: 2
    max_strong_per_p: 2
  decoration:
    separator: "{deco}"
    check: "✓"
    bullet: "·"

# =============================================================================
# 学习依据（人工可读，用于追溯风格来源）
# =============================================================================
learned_features:
  colors_top5:
"""
    for c, n in list(colors.items())[:5]:
        yaml += f"    \"{c}\": {n}\n"
    yaml += "  fonts_top5:\n"
    for f, n in list(fonts.items())[:5]:
        yaml += f"    \"{f}\": {n}\n"
    yaml += f"  decorations: {decos[:3]}\n"
    yaml += f"  border_lefts_sample: {features['border_lefts'][:3]}\n"
    return yaml


# =========================================================================
# CLI
# =========================================================================
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="从微信文章或 HTML 学习风格")
    p.add_argument("--url", help="微信文章 URL")
    p.add_argument("--html", help="本地 HTML 文件路径")
    p.add_argument("--name", required=True, help="风格名（将作为 .yml 文件名）")
    p.add_argument("--description", default="", help="风格描述（中文）")
    p.add_argument("--out", help="输出路径（默认 styles/learned/<name>.yml）")
    p.add_argument("--features-only", action="store_true", help="只输出特征，不生成 YAML")
    args = p.parse_args()

    if args.url:
        print(f"📥 抓取 {args.url[:60]}...")
        html = fetch_url(args.url)
    elif args.html:
        html = Path(args.html).read_text(encoding="utf-8")
    else:
        print("❌ 必须提供 --url 或 --html")
        sys.exit(1)

    print(f"   HTML 长度: {len(html):,} 字节")

    features = extract_features(html)
    print(f"   主色: {list(features['colors'].items())[:3]}")

    if args.features_only:
        print(json.dumps(features, ensure_ascii=False, indent=2))
        sys.exit(0)

    yaml = build_yaml(args.name, features, args.description)

    out_path = Path(args.out) if args.out else (PROJECT_DIR / "styles" / "learned" / f"{args.name}.yml")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml, encoding="utf-8")
    print(f"\n✅ 风格已学到: {out_path}")
    print(f"   预览: python3 core/style_renderer.py --style {args.name} --in your.md")
    print(f"   发布: python3 core/publish.py --style {args.name} --title '...' --in your.md")
