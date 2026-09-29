#!/usr/bin/env python3
"""
公众号文章排版样式模块（亿检链品牌版）

> 来源：本文件规则全部来自 <cwd>/AGENTS.md + <cwd>/images/README.md。
> 用法：任意脚本中 `from tools.article_styles import build_article_html`
>      传入 (title, md_content) 即可得到符合规范的微信富文本 HTML。

## 设计规范速查（与 AGENTS.md 一一对应）

| 元素 | CSS | 来源 |
|------|-----|------|
| H1 主标题 | linear-gradient(135deg,#667eea 0%,#764ba2 100%) | AGENTS.md 标题区 |
| H2 小标题 | linear-gradient(90deg,#667eea22,#764ba222) + 4px solid #667eea | AGENTS.md 小标题 |
| 正文段落 | 15px / line-height 1.9 / color #333 | AGENTS.md 正文段落 |
| 引用块 | #f8f9fa + 4px solid #e94560 | AGENTS.md 引用块（品牌强调色） |
| 加粗 | font-weight:bold; color:#e94560 | AGENTS.md 加粗强调 |
| 分隔线 | border-top:1px solid #eee; margin:25px 0 | AGENTS.md 分隔线 |

## 品牌变化（2026-09 起）
- 公众号名：觉知岛 → 亿检链
- 所有头图必须以官方头图为底图叠加
- 配色从鎏金改为科技蓝（#0a2e7a → #1e6dff）+ 红色强调（#f24c3a）
"""

from __future__ import annotations
import re
from pathlib import Path

# =========================================================================
# 品牌配置（与 config.json["cover"] 一致，可被覆盖）
# =========================================================================
BRAND_DEFAULTS = {
    "brand_name": "亿检链",
    "brand_en": "LIMSCHAIN",
    "parent_brand": "利姆斯科技旗下品牌",
    "slogan": "让企业运营可被验证",
    "sub_slogan": "助力企业成为 AI Native",
    "capabilities": ["可检测", "可决策", "可执行", "可追溯", "可信任"],
    "primary_color": "#0a2e7a",
    "accent_color": "#1e6dff",
    "highlight_red": "#f24c3a",
    # 官方头图路径（绝对或相对 cwd）
    "official_header": "images/亿检链_头图横幅_官方_1920x780.png",
}


# =========================================================================
# 排版样式（与 AGENTS.md 完全一致）
# =========================================================================

H1_STYLE = (
    "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
    "border-radius: 12px; "
    "padding: 30px 20px; "
    "text-align: center; "
    "color: #fff; "
    "font-size: 20px; "
    "font-weight: bold; "
    "text-shadow: 0 2px 4px rgba(0,0,0,0.2);"
)

H2_STYLE = (
    "background: linear-gradient(90deg, #667eea22, #764ba222); "
    "border-left: 4px solid #667eea; "
    "border-radius: 0 6px 6px 0; "
    "padding: 10px 15px; "
    "font-size: 16px; "
    "font-weight: bold; "
    "color: #333;"
)

P_STYLE = "font-size: 15px; line-height: 1.9; color: #333; margin: 8px 0;"
SPACER_STYLE = "margin: 12px 0;"
HR_STYLE = "border: none; border-top: 1px solid #eee; margin: 25px 0;"
QUOTE_STYLE = (
    "background: #f8f9fa; "
    "border-left: 4px solid #e94560; "
    "border-radius: 0 8px 8px 0; "
    "padding: 12px 18px; "
    "color: #555; "
    "font-size: 14px; "
    "margin: 12px 0;"
)
STRONG_STYLE = "font-weight: bold; color: #e94560"
SECTION_STYLE = "padding: 0 5px;"


# =========================================================================
# HTML 片段构造器
# =========================================================================

def esc(text: str) -> str:
    """轻量 HTML 转义"""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def h1(title: str) -> str:
    """主标题（渐变背景条）"""
    return f'<h1 style="{H1_STYLE}">{esc(title)}</h1>'


def h2(subtitle: str) -> str:
    """小标题（左侧渐变竖条）"""
    return f'<h2 style="{H2_STYLE}">{esc(subtitle)}</h2>'


def p(text: str) -> str:
    """正文段落（自动处理 **bold**）"""
    # 把 **xxx** 替换为 <strong style="...">
    html = re.sub(
        r"\*\*(.+?)\*\*",
        lambda m: f'<strong style="{STRONG_STYLE}">{esc(m.group(1))}</strong>',
        esc(text),
    )
    return f'<p style="{P_STYLE}">{html}</p>'


def spacer() -> str:
    return f'<p style="{SPACER_STYLE}">&nbsp;</p>'


def hr() -> str:
    return f'<hr style="{HR_STYLE}">'


def quote(text: str) -> str:
    """引用块（红边 + 浅灰底，全文 ≤ 2 处）"""
    html = re.sub(
        r"\*\*(.+?)\*\*",
        lambda m: f'<strong style="{STRONG_STYLE}">{esc(m.group(1))}</strong>',
        esc(text),
    )
    return f'<blockquote style="{QUOTE_STYLE}">{html}</blockquote>'


def image_md_hint(desc: str) -> str:
    """正文配图占位（Markdown 风格，用于发布脚本识别）"""
    return f"[配图：{desc}]"


def wrap_section(html: str) -> str:
    """全文用 <section padding=5> 包裹"""
    return f'<section style="{SECTION_STYLE}">\n\n{html}\n\n</section>'


# =========================================================================
# 一键拼装：把 Markdown 转成符合 AGENTS.md 的微信富文本 HTML
# =========================================================================

def build_article_html(title: str, md_body: str) -> str:
    """
    将 Markdown 文章体渲染为符合 AGENTS.md 规范的微信富文本 HTML。

    支持的 Markdown 元素：
      # 标题（首段作为 H1）
      ## 二级标题（作为 H2）
      > 引用（含注释/加粗）
      **加粗**（品牌红色 #e94560）
      --- （分割线）
      空行（段落间隔）
      普通段落
    """
    lines = md_body.split("\n")
    parts: list[str] = []

    first_h1_emitted = False
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        # 空行 → 间隔
        if not stripped:
            parts.append(spacer())
            continue

        # 主标题（H1 一次，且作为页面顶部装饰）
        if stripped.startswith("# ") and not stripped.startswith("## "):
            if not first_h1_emitted:
                parts.append(h1(stripped[2:].strip()))
                parts.append(spacer())
                first_h1_emitted = True
            continue

        # 二级标题
        if stripped.startswith("## "):
            parts.append(h2(stripped[3:].strip()))
            parts.append(spacer())
            continue

        # 分隔线
        if stripped == "---":
            parts.append(hr())
            parts.append(spacer())
            continue

        # 引用
        if stripped.startswith("> "):
            parts.append(quote(stripped[2:].strip()))
            parts.append(spacer())
            continue

        # 普通段落（首尾空段已加 spacer，这里只渲染内容）
        parts.append(p(stripped))

    return wrap_section("\n".join(parts))


def count_chinese_chars(html: str) -> int:
    """统计中文字数（含 <strong> 标签内的字符）"""
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&nbsp;", "").replace("&amp;", "&")
    return sum(1 for c in text if "一" <= c <= "鿿")


# =========================================================================
# 自检（开发调试用）
# =========================================================================
if __name__ == "__main__":
    sample_md = """# 测试标题：一行不超过60字

你是不是也遇到过这种情况？

## 一、第一个小标题

正文段落。**核心观点加粗**。

> 一句金句。

## 二、第二个小标题

正文段落。**加粗关键词**。

---

> 结尾金句。
"""
    html = build_article_html("测试标题：一行不超过60字", sample_md)
    print(html)
    print(f"\n字数: {count_chinese_chars(html)}")