#!/usr/bin/env python3
"""
风格化发布器：从 markdown + 风格 → 微信公众号草稿箱

> 特性：
> 1. 内联图片处理：自动解析 ![alt](path)、上传到微信 CDN、替换为微信 URL
> 2. 品牌头图插入：固定复用同一张 brand_header 图（缓存 media_id，不再每次重传）
> 3. 正确的 digest：从 markdown 取纯文本，不用 HTML 头标签
> 4. 风格化渲染：调用 core/style_renderer.StyleRenderer
> 5. 旧素材清理：删除旧草稿时，主动 delete 关联的封面图 / 品牌头图（永久素材）

> 版本：
> - v1.0 (2026-10-01): 统一发布入口（原 core/publish_v2.py 重命名）；
>   包含品牌头图缓存 + 永久素材清理 + 摘要从 markdown 提取

用法：
    from core.publish import publish_with_style
    result = publish_with_style(
        title="...",
        md_text="...",
        style_name="warm_gold",
        cover_image_path="...",                  # thumb_media_id（公众号推送大图）
        brand_header_path="...",                 # 正文顶部品牌头图（可选；不传则用项目默认）
        delete_old_media_id="...",               # 旧草稿 media_id（用于覆盖发布）
        delete_old_cover_media_id="...",         # 顺手清理旧封面图（永久素材）
        delete_old_brand_media_id="...",         # 顺手清理旧品牌头图（永久素材）
    )

    # CLI
    python3 core/publish.py --style warm_gold --title "..." \\
        --in content.md --cover cover.png \\
        --delete-old bLecvU4Iq3Pp... \\
        --delete-old-cover XXXXXXXXX \\
        --delete-old-brand YYYYYYYYY
"""
from __future__ import annotations
import os, sys, re, json, requests
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from core.publisher import WeChatPublisher
from core.style_renderer import StyleRenderer, list_styles


# 固定品牌头图默认路径（项目内 images/ 目录里的横幅）
DEFAULT_BRAND_HEADER = PROJECT_DIR / "images" / "亿检链_头图横幅_900x383.png"

# 品牌头图缓存：复用 media_id 避免每次重新上传
BRAND_HEADER_CACHE_PATH = PROJECT_DIR / "outputs" / ".brand_header_cache.json"


# =========================================================================
# 摘要生成（从 markdown，不从 HTML）
# =========================================================================
def _make_digest_from_md(md: str, max_len: int = 80) -> str:
    """从 markdown 提取纯文本摘要

    去掉 markdown 标记（# ## > ** --- []()），取前 max_len 字。
    """
    # 按行处理
    lines = []
    for line in md.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("---"):
            continue
        if s.startswith(">"):
            s = s.lstrip(">").strip()
        if s.startswith("!["):
            # 图片标记，跳过
            continue
        # 去掉 ** 加粗
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        # 去掉 [text](url) 中的 [text]
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        if s:
            lines.append(s)
    plain = " ".join(lines)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) > max_len:
        plain = plain[:max_len] + "…"
    return plain


# =========================================================================
# 内联图片处理
# =========================================================================
def _resolve_inline_path(path: str) -> str | None:
    """把 markdown 中的相对路径解析为绝对路径

    支持：
        ./inline_xxx.png       → outputs/inline_xxx.png 或 output/inline_xxx.png
        outputs/inline_xxx.png → 原样
        /full/path/to/image     → 原样
        http(s)://...          → 返回 None（远程图，不处理）
    """
    if path.startswith(("http://", "https://", "data:")):
        return None  # 远程图，不下载不处理
    if path.startswith("./"):
        # 去掉 ./，按优先级找
        stem = path[2:]
        candidates = [
            PROJECT_DIR / "outputs" / stem,
            PROJECT_DIR / "output" / stem,
            PROJECT_DIR / "images" / stem,
            PROJECT_DIR / stem,
            Path(os.getcwd()) / stem,
        ]
        for c in candidates:
            if c.exists():
                return str(c)
    if path.startswith("/"):
        return path if Path(path).exists() else None
    # 相对路径
    full = PROJECT_DIR / path
    if full.exists():
        return str(full)
    return None


def _process_inline_images(token: str, publisher: WeChatPublisher,
                           html: str) -> tuple[str, list[str]]:
    """扫描 HTML 里的 <img src="" />，把本地路径上传到微信 CDN，返回新 HTML

    仅处理 src 是本地路径的图片（不是 http(s)/data）。
    返回 (新 HTML, 上传成功的 URL 列表)
    """
    pattern = re.compile(r'(<img\b[^>]*?\bsrc=)"([^"]+)"')
    uploaded_urls = []

    def replace(m):
        prefix = m.group(1)
        src = m.group(2)
        # 远程图不处理
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        # 解析本地路径
        local = _resolve_inline_path(src)
        if not local:
            return m.group(0)
        # 上传到微信
        url = publisher._upload_image(token, local, is_inline=True)
        if url:
            uploaded_urls.append(url)
            return f'{prefix}"{url}"'
        return m.group(0)

    new_html = pattern.sub(replace, html)
    return new_html, uploaded_urls


# =========================================================================
# 品牌头图（固定素材 + 缓存）
# =========================================================================
def _load_brand_cache() -> dict | None:
    """读取品牌头图缓存（{path, mtime, media_id, url}）"""
    if not BRAND_HEADER_CACHE_PATH.exists():
        return None
    try:
        return json.loads(BRAND_HEADER_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_brand_cache(record: dict) -> None:
    """保存品牌头图缓存到 outputs/.brand_header_cache.json"""
    BRAND_HEADER_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BRAND_HEADER_CACHE_PATH.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _get_or_upload_brand_header(token: str, publisher: WeChatPublisher,
                                 brand_header_path: str | Path) -> tuple[str, str | None]:
    """获取品牌头图的微信 URL

    策略：
    - 如果 path 已上传过（缓存命中：path + mtime 一致），复用之前的 URL + media_id
    - 否则重新上传并缓存

    返回 (微信 URL, 永久素材 media_id 或 None)
    """
    path = Path(brand_header_path).resolve()
    if not path.exists():
        return "", None

    cache = _load_brand_cache()
    current_mtime = path.stat().st_mtime

    if (cache
        and cache.get("path") == str(path)
        and cache.get("mtime") == current_mtime):
        # 命中缓存：URL 和 media_id 都可以复用
        print(f"  🏷️  品牌头图复用缓存: {path.name}")
        return cache.get("url", ""), cache.get("media_id")

    # 重新上传：先拿到微信 URL（用于正文 <img>）
    url = publisher._upload_image(token, str(path), is_inline=True)
    if not url:
        return "", None

    # 永久素材接口：拿 media_id（用于主动删除）
    media_id = publisher._upload_image(token, str(path), is_inline=False)

    _save_brand_cache({
        "path": str(path),
        "mtime": current_mtime,
        "url": url,
        "media_id": media_id,
        "uploaded_at": __import__("datetime").datetime.now().isoformat(),
    })
    print(f"  🏷️  品牌头图首次上传: media_id={media_id}")
    return url, media_id


def _build_brand_header_html(url: str) -> str:
    """构建品牌头图的 HTML 片段（传入已上传的微信 URL）"""
    if not url:
        return ""
    return (
        f'<section style="margin: 0 0 16px 0; text-align: center;">'
        f'<img src="{url}" alt="亿检链" style="width: 100%; max-width: 100%; border-radius: 12px;" />'
        f'</section>'
    )


# =========================================================================
# 永久素材清理
# =========================================================================
def _delete_material(token: str, media_id: str) -> bool:
    """删除公众号永久素材（封面图、语音、视频等）

    注意：图文内联图片（uploadimg 返回的 URL）走的是临时素材通道，没有删除接口，
    微信 3 天自动清理。这是微信 API 限制，不是工具 bug。
    """
    if not media_id:
        return False
    url = "https://api.weixin.qq.com/cgi-bin/material/del_material"
    try:
        resp = requests.post(
            url + f"?access_token={token}",
            data=json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=10,
        )
        result = resp.json()
        if result.get("errcode") == 0:
            print(f"  🧹 已清理旧素材: {media_id[:20]}...")
            return True
        else:
            print(f"  ⚠️  清理旧素材失败: {result}")
            return False
    except Exception as e:
        print(f"  ⚠️  清理旧素材异常: {e}")
        return False


# =========================================================================
# 主入口
# =========================================================================
def publish_with_style(
    title: str,
    md_text: str,
    style_name: str = "tech_blue",
    cover_image_path: str = None,
    brand_header_path: str = None,
    delete_old_media_id: str = None,
    delete_old_cover_media_id: str = None,
    delete_old_brand_media_id: str = None,
) -> dict | None:
    """完整流程：md + style + 内联图片处理 + 品牌头图 → 微信草稿箱

    参数：
        title: 文章标题（≤ 64 字）
        md_text: 完整 markdown（含 # 标题、## 小标题、> 引用、---、**加粗**、![alt](path)）
        style_name: 风格名（默认 tech_blue）
        cover_image_path: 封面图本地路径（thumb_media_id，推送顶部大图）
        brand_header_path: 品牌头图本地路径（不传则用项目默认 images/亿检链_头图横幅_900x383.png）
        delete_old_media_id: 要删除的旧草稿 media_id（用于覆盖发布）
        delete_old_cover_media_id: 顺手清理旧封面图（永久素材 media_id）
        delete_old_brand_media_id: 顺手清理旧品牌头图（永久素材 media_id，缓存变更时才需要）

    返回：
        dict 包含：
          - media_id: 新草稿 media_id
          - thumb_media_id: 新封面图 media_id（永久素材，下次可一并清理）
          - brand_media_id: 新品牌头图 media_id（永久素材，下次可一并清理）
          - inline_urls: 本次上传的内联图片 URL 列表（无法主动清理）
        或 None（失败）
    """
    publisher = WeChatPublisher()
    token = publisher._get_access_token()
    if not token:
        return None

    # 0. 清理旧资源（先删草稿，再删永久素材）
    if delete_old_media_id:
        delete_url = "https://api.weixin.qq.com/cgi-bin/draft/delete"
        resp = requests.post(
            delete_url + f"?access_token={token}",
            data=json.dumps({"media_id": delete_old_media_id}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        result = resp.json()
        if result.get("errcode") == 0:
            print(f"  🗑️  已删除旧草稿: {delete_old_media_id[:20]}...")
        else:
            print(f"  ⚠️  删除旧草稿失败: {result}")

    # 清理旧封面图（永久素材，可删）
    if delete_old_cover_media_id:
        _delete_material(token, delete_old_cover_media_id)

    # 清理旧品牌头图（永久素材，可删）
    if delete_old_brand_media_id:
        _delete_material(token, delete_old_brand_media_id)

    # 1. 渲染 HTML（按风格）
    renderer = StyleRenderer(style_name)
    html = renderer.render(md_text)

    # 2. 内联图片处理（上传到微信 CDN）
    html, inline_urls = _process_inline_images(token, publisher, html)
    if inline_urls:
        print(f"  📷 已上传 {len(inline_urls)} 张内联图片到微信 CDN（URL 3 天后自动回收）")

    # 3. 品牌头图插入（正文顶部）—— 复用缓存，不再每次重传
    brand_header_html = ""
    brand_media_id = None
    actual_brand_path = None
    if brand_header_path and Path(brand_header_path).exists():
        actual_brand_path = brand_header_path
    elif DEFAULT_BRAND_HEADER.exists():
        actual_brand_path = DEFAULT_BRAND_HEADER

    if actual_brand_path:
        brand_url, brand_media_id = _get_or_upload_brand_header(token, publisher, actual_brand_path)
        brand_header_html = _build_brand_header_html(brand_url)
        if brand_header_html:
            print(f"  🏷️  品牌头图已置入正文（path={Path(actual_brand_path).name}）")
    else:
        print(f"  ℹ️  未提供品牌头图（跳过）")

    # 4. 拼接最终 HTML
    final_html = brand_header_html + html if brand_header_html else html

    # 5. GEO JSON-LD
    keywords = publisher._make_keywords(title, final_html)
    digest = _make_digest_from_md(md_text)  # 用 markdown 而非 HTML 取摘要
    jsonld = publisher._build_jsonld(title, digest, keywords)
    jsonld_script = f'<script type="application/ld+json">{jsonld}</script>'

    # 用 <article> 包裹
    final_html = f'<article>{jsonld_script}{final_html}</article>'

    # 6. 上传封面图（thumb_media_id）
    thumb_media_id = None
    if cover_image_path and Path(cover_image_path).exists():
        thumb_media_id = publisher._upload_image(token, str(Path(cover_image_path).resolve()))

    # 7. 推送到草稿箱
    article = {
        "title": title,
        "author": "顺道大叔",
        "content": final_html,
        "content_source_url": "",
        "digest": digest,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id

    payload = {"articles": [article]}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(
        publisher.cfg["draft_url"] + f"?access_token={token}",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    result = resp.json()
    if "media_id" in result:
        new_media_id = result["media_id"]
        print(f"  ✅ 已发布（风格={style_name}）media_id={new_media_id}")
        return {
            "media_id": new_media_id,
            "thumb_media_id": thumb_media_id,
            "brand_media_id": brand_media_id,
            "inline_urls": inline_urls,
        }
    else:
        print(f"  ❌ 保存草稿失败: {result}")
        return None


# =========================================================================
# CLI
# =========================================================================
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="按风格发布 markdown 到公众号草稿箱")
    p.add_argument("--style", default="tech_blue", help="风格名（默认 tech_blue）")
    p.add_argument("--list-styles", action="store_true", help="列出所有风格")
    p.add_argument("--title", help="文章标题")
    p.add_argument("--in", dest="input", help="输入 markdown 路径")
    p.add_argument("--cover", help="封面图路径（thumb_media_id，推送顶部大图）")
    p.add_argument("--brand-header", help="品牌头图路径（插入正文顶部）")
    p.add_argument("--delete-old", help="删除指定 media_id 的旧草稿")
    p.add_argument("--delete-old-cover", help="顺手清理旧封面图（永久素材 media_id）")
    p.add_argument("--delete-old-brand", help="顺手清理旧品牌头图（永久素材 media_id）")
    args = p.parse_args()

    if args.list_styles:
        print("已注册风格：")
        for s in list_styles():
            learned = " [learned]" if s.get("learned") else ""
            tags = ", ".join(s.get("tags", []))
            print(f"  - {s['name']:18s} {s.get('display_name', '')}{learned}")
            if tags:
                print(f"    tags: {tags}")
        sys.exit(0)

    if not args.title:
        print("❌ 必须提供 --title")
        sys.exit(1)

    md_text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()

    result = publish_with_style(
        title=args.title,
        md_text=md_text,
        style_name=args.style,
        cover_image_path=args.cover if args.cover and Path(args.cover).exists() else None,
        brand_header_path=args.brand_header if args.brand_header and Path(args.brand_header).exists() else None,
        delete_old_media_id=args.delete_old,
        delete_old_cover_media_id=args.delete_old_cover,
        delete_old_brand_media_id=args.delete_old_brand,
    )
    if result:
        print(f"\n✅ 完成。新草稿 media_id: {result['media_id']}")
        print(f"   封面图 media_id: {result.get('thumb_media_id', 'N/A')}")
        print(f"   品牌头图 media_id: {result.get('brand_media_id', 'N/A')}")
        print(f"   下次覆盖发布时，可用：")
        print(f"     --delete-old {result['media_id']}")
        if result.get("thumb_media_id"):
            print(f"     --delete-old-cover {result['thumb_media_id']}")
        if result.get("brand_media_id"):
            print(f"     --delete-old-brand {result['brand_media_id']}")
        sys.exit(0)
    else:
        print(f"\n❌ 失败")
        sys.exit(1)
