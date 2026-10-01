#!/usr/bin/env python3
"""
风格渲染器：markdown + style_name → 微信富文本 HTML

> **唯一入口**：所有 markdown → HTML 的转换必须走这个模块。
> 禁止在脚本里直接拼内联 CSS。

用法：
    from core.style_renderer import StyleRenderer
    r = StyleRenderer("warm_gold")
    html = r.render(md_text)

    # CLI 用法
    python3 core/style_renderer.py --style warm_gold --in article.md --out article.html
"""
from __future__ import annotations
import re
import sys
import yaml
from pathlib import Path
from typing import Optional

PROJECT_DIR = Path(__file__).parent.parent
STYLES_DIR = PROJECT_DIR / "styles"


# =========================================================================
# YAML 加载（容错：依赖 PyYAML 时使用，否则用简易解析）
# =========================================================================
def _yaml_safe_load(path: Path) -> dict:
    """加载 YAML；优先用 PyYAML，回退到内置 json"""
    text = path.read_text(encoding="utf-8")
    # 去掉注释行（# 开头）但保留字符串内的 #
    lines = []
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        # 去掉行尾注释（不在引号内的 #）
        if "#" in line:
            # 简单处理：找到第一个不在引号内的 #
            in_quote = False
            for i, ch in enumerate(line):
                if ch in ('"', "'"):
                    in_quote = not in_quote
                elif ch == "#" and not in_quote:
                    lines.append(line[:i].rstrip())
                    break
            else:
                lines.append(line)
        else:
            lines.append(line)
    text = "\n".join(lines)
    try:
        return yaml.safe_load(text)
    except ImportError:
        # 回退：用 json（要求 YAML 是合法 JSON 子集）
        import json
        # 简单把 YAML 转 JSON
        # 第一层 key 缩进必须一致
        return _mini_yaml_parse(text)


def _mini_yaml_parse(text: str) -> dict:
    """极简 YAML 解析器（仅支持本项目风格文件结构）"""
    result = {}
    lines = text.split("\n")
    stack = [(-1, result)]  # (indent, dict_or_list)
    current_list = None
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        content = line.strip()
        # 弹出更深缩进
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if ":" in content:
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()
            if not val:
                # 嵌套对象
                new = {}
                parent[key] = new
                stack.append((indent, new))
            else:
                # 标量
                v = _parse_scalar(val)
                parent[key] = v
        elif content.startswith("- "):
            # 列表项
            item_content = content[2:]
            if not current_list or current_list[0] != indent:
                # 这里不严格支持复杂列表，跳过
                pass
    return result


def _parse_scalar(s: str):
    """解析 YAML 标量"""
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.lower() in ("true", "yes"):
        return True
    if s.lower() in ("false", "no"):
        return False
    if s.lower() in ("null", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


# =========================================================================
# 风格加载
# =========================================================================
class Style:
    """单个风格的运行时表示"""
    def __init__(self, data: dict, source_path: Path):
        self.data = data
        self.meta = data.get("meta", {})
        self.palette = data.get("palette", {})
        self.components = data.get("components", {})
        self.rendering = data.get("rendering", {})
        self.source_path = source_path
        self.name = self.meta.get("name", source_path.stem)

    def __repr__(self):
        return f"<Style {self.name} ({self.meta.get('display_name', '')})>"


def load_style(name: str) -> Style:
    """加载指定风格的 YAML

    查找顺序：
        styles/<name>.yml
        styles/learned/<name>.yml
    """
    for sub in ("", "learned"):
        p = STYLES_DIR / sub / f"{name}.yml"
        if p.exists():
            return Style(_yaml_safe_load(p), p)
    raise FileNotFoundError(f"风格未注册: {name}（查找路径: {STYLES_DIR}/<name>.yml）")


def list_styles() -> list[dict]:
    """列出所有可用风格"""
    out = []
    for p in sorted(STYLES_DIR.glob("*.yml")):
        try:
            s = load_style(p.stem)
            out.append({
                "name": s.name,
                "display_name": s.meta.get("display_name", s.name),
                "tags": s.meta.get("tags", []),
                "source": s.meta.get("source_url", ""),
                "path": str(p.relative_to(PROJECT_DIR)),
            })
        except Exception as e:
            out.append({"name": p.stem, "error": str(e)})
    for p in sorted((STYLES_DIR / "learned").glob("*.yml")):
        try:
            s = load_style(p.stem)
            out.append({
                "name": s.name,
                "display_name": s.meta.get("display_name", s.name),
                "tags": s.meta.get("tags", []),
                "source": s.meta.get("source_url", ""),
                "path": str(p.relative_to(PROJECT_DIR)),
                "learned": True,
            })
        except Exception as e:
            out.append({"name": p.stem, "error": str(e)})
    return out


# =========================================================================
# 文本处理工具
# =========================================================================
def _esc(text: str) -> str:
    """HTML escape"""
    return (text.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


def _inline_md_to_html(text: str, strong_style: str) -> str:
    """把段落内的 markdown 标记转 HTML：
       **xxx** → <strong style="...">xxx</strong>
       自动跳过孤立的 **（如 **）或 *xxx*
    """
    # 处理 **xxx** 加粗（非贪婪，需要前后成对）
    pattern = re.compile(r"\*\*(.+?)\*\*")

    def _strong(m):
        inner = _esc(m.group(1))
        return f'<strong style="{strong_style}">{inner}</strong>'

    text = pattern.sub(_strong, text)
    return text


# =========================================================================
# 核心渲染器
# =========================================================================
class StyleRenderer:
    def __init__(self, style_name: str):
        self.style = load_style(style_name)
        self.c = self.style.components
        self.p = self.style.palette
        self.rendering = self.style.rendering

    # ------- 元素构造器 -------
    def _h1(self, title: str) -> str:
        c = self.c["h1"]
        # 两种风格：
        #   A. 渐变背景条（h1.title 自带 background）
        #   B. 纯文字 + 装饰线（h1.container + h1.title + h1.deco）
        title_html = _esc(title)
        if "background" in c["title"]:
            # A 型：渐变背景条
            return (f'<section style="{c["container"]}">'
                    f'<h1 style="{c["title"]}">{title_html}</h1>'
                    f'</section>')
        else:
            # B 型：纯文字 + 装饰线
            return (f'<section style="{c["container"]}">'
                    f'<h1 style="{c["title"]}">{title_html}</h1>'
                    f'<section style="{c["deco"]}"></section>'
                    f'</section>')

    def _h2(self, sub: str) -> str:
        c = self.c["h2"]
        # 两种风格：
        #   A. 单一 title（带 background）
        #   B. flex 布局（container + flex + bar + title）
        sub_html = _esc(sub)
        if "flex" in c:
            return (f'<section style="{c["container"]}">'
                    f'<section style="{c["flex"]}">'
                    f'<section style="{c["bar"]}"></section>'
                    f'<h3 style="{c["title"]}">{sub_html}</h3>'
                    f'</section></section>')
        else:
            return f'<h2 style="{c["title"]}">{sub_html}</h2>'

    def _h3(self, sub: str) -> str:
        c = self.c["h3"]
        sub_html = _esc(sub)
        if "title" in c:
            return (f'<section style="{c["container"]}">'
                    f'<h3 style="{c["title"]}">{sub_html}</h3>'
                    f'</section>')
        return f'<h3 style="{c["title"]}">{sub_html}</h3>'

    def _p(self, text: str) -> str:
        c = self.c["p"]
        strong_style = self.c["strong"]["base"]
        # 转义后再处理加粗
        text_html = _inline_md_to_html(text, strong_style)
        return f'<p style="{c["base"]}">{text_html}</p>'

    def _blockquote(self, lines: list[str]) -> str:
        c = self.c["blockquote"]
        strong_style = self.c["strong"]["base"]
        # 多行引用合并
        joined = " ".join(line.lstrip(">").strip() for line in lines)
        inner_html = _inline_md_to_html(joined, strong_style)
        if "container" in c and "flex" not in c.get("container", ""):
            # 风格 A：单一容器 + 文本样式
            text_style = c.get("text", "")
            text_attrs = f' style="{text_style}"' if text_style else ""
            return (f'<section style="{c["container"]}">'
                    f'<p{text_attrs}>{inner_html}</p>'
                    f'</section>')
        else:
            # 风格 B：单段落引用
            return f'<p style="{c["container"]}">{inner_html}</p>'

    def _hr(self) -> str:
        c = self.c["hr"]
        if c.get("content"):
            # 字符装饰
            return (f'<section style="{c["container"]}">'
                    f'{c["content"]}</section>')
        # 标准 <hr>
        return f'<hr style="{c.get("style", "border: none; border-top: 1px solid #eee; margin: 25px 0;")}>'

    def _spacer(self) -> str:
        return f'<p style="{self.c["spacer"]["base"]}">&nbsp;</p>'

    def _section_open(self) -> str:
        section_style = self.c["section"]["base"].rstrip(";")
        return f'<section style="{section_style}; font-family: -apple-system, BlinkMacSystemFont, \'PingFang SC\', \'Microsoft YaHei\', sans-serif;">'

    def _section_close(self) -> str:
        return "</section>"

    def _img(self, alt: str, path: str = "") -> str:
        c = self.c["img"]
        return (f'<section style="{c["base"]}">'
                f'<img src="{_esc(path)}" alt="{_esc(alt)}" style="{c["img"]}" />'
                f'</section>')

    # ------- 主入口 -------
    def render(self, md_text: str, title: Optional[str] = None,
               inline_images: Optional[dict] = None) -> str:
        """把 markdown 渲染为微信富文本 HTML

        参数：
            md_text:  完整 markdown（含 # 标题、## 小标题、> 引用、---、**加粗**）
            title:    可选，文章主标题（如果 md_text 第一行不是 # 标题）
            inline_images: 可选，dict {占位符: URL} 用于替换文中 ![alt](url) 占位
        """
        lines = md_text.split("\n")
        parts: list[str] = []
        first_h1 = True
        max_blockquotes = self.rendering.get("limits", {}).get("max_blockquotes", 2)
        quote_count = 0
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            stripped = line.strip()

            # 空行 → 空行
            if not stripped:
                parts.append(self._spacer())
                i += 1
                continue

            # # 标题
            if stripped.startswith("# ") and not stripped.startswith("## "):
                if first_h1:
                    parts.append(self._h1(stripped[2:].strip()))
                    parts.append(self._spacer())
                    first_h1 = False
                i += 1
                continue

            # ## 小标题
            if stripped.startswith("## "):
                parts.append(self._h2(stripped[3:].strip()))
                parts.append(self._spacer())
                i += 1
                continue

            # ### 三级标题
            if stripped.startswith("### "):
                parts.append(self._h3(stripped[4:].strip()))
                parts.append(self._spacer())
                i += 1
                continue

            # 分隔线 ---
            if stripped == "---":
                parts.append(self._hr())
                parts.append(self._spacer())
                i += 1
                continue

            # 引用（可能跨多行）
            if stripped.startswith(">"):
                quote_lines = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    quote_lines.append(lines[i])
                    i += 1
                if quote_count < max_blockquotes:
                    parts.append(self._blockquote(quote_lines))
                    parts.append(self._spacer())
                    quote_count += 1
                else:
                    for ql in quote_lines:
                        clean = ql.strip().lstrip(">").strip()
                        if clean:
                            parts.append(self._p(clean))
                            parts.append(self._spacer())
                continue

            # 图片
            img_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
            if img_match:
                alt = img_match.group(1)
                path = img_match.group(2)
                # 支持 inline_images 占位替换
                if inline_images and path in inline_images:
                    path = inline_images[path]
                parts.append(self._img(alt, path))
                i += 1
                continue

            # 普通段落
            parts.append(self._p(stripped))
            i += 1

        # 如果传了 title 但 md 里没出现 H1，补一个
        if title and first_h1:
            parts.insert(0, self._h1(title))
            parts.insert(1, self._spacer())

        body = "\n".join(parts)
        return self._section_open() + "\n\n" + body + "\n\n" + self._section_close()


# =========================================================================
# CLI
# =========================================================================
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="按风格渲染 markdown → 微信 HTML")
    p.add_argument("--style", default="tech_blue", help="风格名（默认 tech_blue）")
    p.add_argument("--list", action="store_true", help="列出所有风格")
    p.add_argument("--in", dest="input", help="输入 markdown 文件路径")
    p.add_argument("--out", help="输出 HTML 文件路径")
    p.add_argument("--title", help="可选，文章标题（覆盖 md 第一行）")
    args = p.parse_args()

    if args.list:
        print("已注册风格：")
        for s in list_styles():
            learned = " [learned]" if s.get("learned") else ""
            tags = ", ".join(s.get("tags", []))
            print(f"  - {s['name']:20s} {s.get('display_name', '')}{learned}")
            if tags:
                print(f"    tags: {tags}")
        sys.exit(0)

    md_text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    renderer = StyleRenderer(args.style)
    html = renderer.render(md_text, title=args.title)
    if args.out:
        Path(args.out).write_text(html, encoding="utf-8")
        print(f"✅ 已渲染: {args.out} ({len(html)} 字节)")
    else:
        print(html)
