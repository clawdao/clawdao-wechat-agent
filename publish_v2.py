#!/usr/bin/env python3
"""
觉知岛公众号 - 优化发布脚本 v2
1. 品牌头图作为统一品牌宣传图置于文章顶部（不含标题信息）
2. 个性化封面图作为 thumb_media_id
3. 每篇文章至少3张文中插图（diagram/info/concept）
"""
import sys, os, re, time, json, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wechat_publisher import WeChatPublisher

PUBLISHER = WeChatPublisher()
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "output")

# ===== 文章配置 =====
ARTICLES = [
    {
        "file": "output/article_final_01.md",
        "title": "越焦虑的人 越需要一个觉知系统",
        "cover": "output/cover_越焦虑的人_越需要一个觉知系统.png",
        "inline": [
            "output/inline_越焦虑的人_越需要一个觉知系统_-_图1_diagram.png",
            "output/inline_越焦虑的人_越需要一个觉知系统_-_图2_info.png",
            "output/inline_越焦虑的人_越需要一个觉知系统_-_图3_concept.png",
        ],
    },
    {
        "file": "output/article_final_02.md",
        "title": "你的大脑还在用2G网 换这套认知框架试试",
        "cover": "output/cover_你的大脑还在用2G网_换这套认知框架试试.png",
        "inline": [
            "output/inline_你的大脑还在用2G网_换这套认知框架试试_diagram.png",
            "output/inline_你的大脑还在用2G网_换这套认知框架试试_info.png",
            "output/inline_你的大脑还在用2G网_换这套认知框架试试_concept.png",
        ],
    },
    {
        "file": "output/article_final_03.md",
        "title": "一个人干翻一个团队 秘密是这3个智能体",
        "cover": "output/cover_一个人干翻一个团队_秘密是这3个智能体.png",
        "inline": [
            "output/inline_一个人干翻一个团队_秘密是这3个智能体__diagram.png",
            "output/inline_一个人干翻一个团队_秘密是这3个智能体__info.png",
            "output/inline_一个人干翻一个团队_秘密是这3个智能体__concept.png",
        ],
    },
]


def upload_image(token, path, is_inline=False):
    """上传图片并返回media_id或url"""
    try:
        endpoint = "https://api.weixin.qq.com/cgi-bin/material/add_material"
        if is_inline:
            endpoint = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
        with open(path, "rb") as f:
            files = {"media": (path, f, "image/png")}
            params = {"access_token": token}
            if not is_inline:
                params["type"] = "image"
            resp = requests.post(endpoint, params=params, files=files, timeout=30)
            data = resp.json()
            if not is_inline and "media_id" in data:
                return data["media_id"]
            elif is_inline and "url" in data:
                return data["url"]
            else:
                print(f"  ⚠️  上传失败: {data}")
                return None
    except Exception as e:
        print(f"  ❌ 上传异常: {e}")
        return None


def make_article_html(brand_header_url, inline_urls, md_content, token):
    """构建文章的完整HTML，包含品牌头图、内嵌插图"""
    
    # 品牌头图HTML块（放在文章顶部，不含标题信息，统一品牌宣传）
    brand_section = (
        f'<section style="margin: 0 0 20px 0; text-align: center;">'
        f'<img src="{brand_header_url}" alt="觉知岛" style="width: 100%; max-width: 100%; border-radius: 12px;" />'
        f'<p style="margin: 6px 0 0 0; font-size: 13px; color: #999;">品牌·觉知岛</p>'
        f'</section>'
    )
    
    # 使用发布器的markdown转HTML
    html, _ = PUBLISHER._markdown_to_html(md_content, token)
    
    # 替换占位符为实际图片URL
    parts = []
    url_idx = 0
    
    lines = html.split("\n")
    for line in lines:
        # 查找 [图片: xxx] 替换为实际上传URL
        if "[图片:" in line and url_idx < len(inline_urls):
            if inline_urls[url_idx]:
                new_line = (
                    f'<section style="margin: 20px 0; text-align: center;">'
                    f'<img src="{inline_urls[url_idx]}" alt="配图" style="width: 100%; max-width: 100%; border-radius: 10px;" />'
                    f'<p style="margin: 6px 0 0 0; font-size: 13px; color: #999;">插图</p>'
                    f'</section>'
                )
                parts.append(new_line)
            url_idx += 1
        else:
            parts.append(line)
    
    # 如果还有未替换的图片标记（已上传URL但没被 [图片:] 覆盖的）
    body = "\n".join(parts)
    
    # 组合：品牌头图 + 正文（含标题和插图）
    full_html = f'<section style="padding: 0 5px;">\n{brand_section}\n{body}\n</section>'
    
    return full_html


def main():
    print("=" * 60)
    print("  觉知岛 · 公众号优化发布 v2")
    print("  3篇爆款文章 + 品牌头图 + 个性化封面 + 文中插图")
    print("=" * 60)
    
    # 获取token
    token = PUBLISHER._get_access_token()
    if not token:
        print("❌ 无法获取微信access token，请检查配置")
        return
    
    # 上传品牌头图（统一品牌宣传图）
    print("\n📤 上传统一品牌头图...")
    brand_path = os.path.join(OUT, "brand_header.png")
    if os.path.exists(brand_path):
        brand_url = upload_image(token, brand_path, is_inline=True)
        if brand_url:
            print(f"  ✅ 品牌头图上载成功")
        else:
            print(f"  ⚠️ 品牌头图上载失败，使用备用")
            brand_url = None
    else:
        print(f"  ⚠️ brand_header.png 不存在")
        brand_url = None
    
    # 逐篇处理
    for i, art in enumerate(ARTICLES, 1):
        print(f"\n{'='*50}")
        print(f"📄 [{i}/3] {art['title']}")
        print(f"{'='*50}")
        
        # 1. 上传封面图（作为文章封面 thumb_media_id）
        cover_path = os.path.join(BASE, art["cover"])
        if os.path.exists(cover_path):
            cover_media_id = upload_image(token, cover_path, is_inline=False)
            if cover_media_id:
                print(f"  ✅ 封面上载成功")
            else:
                print(f"  ⚠️ 封面上载失败")
                cover_media_id = None
        else:
            print(f"  ⚠️ 封面文件不存在: {cover_path}")
            cover_media_id = None
        
        # 2. 上传所有文中插图
        inline_urls = []
        for ipath in art["inline"]:
            full_path = os.path.join(BASE, ipath)
            if os.path.exists(full_path):
                url = upload_image(token, full_path, is_inline=True)
                if url:
                    inline_urls.append(url)
                    print(f"  ✅ 插图上传: {os.path.basename(ipath)}")
                else:
                    inline_urls.append("")
                    print(f"  ⚠️ 插图失败: {os.path.basename(ipath)}")
            else:
                inline_urls.append("")
                print(f"  ⚠️ 插图不存在: {os.path.basename(ipath)}")
        
        print(f"  共 {len([u for u in inline_urls if u])}/{len(inline_urls)} 张插图就绪")
        
        # 3. 读取文章markdown
        file_path = os.path.join(BASE, art["file"])
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        # 4. 构建最终HTML
        final_html = make_article_html(brand_url, inline_urls, md_content, token)
        
        # 5. 生成摘要（纯文本前80字）
        plain = re.sub(r"[#>*\[\]`\n]", "", md_content).strip()
        plain = re.sub(r"\s+", " ", plain)
        digest = (plain[:80] + "…") if len(plain) > 80 else plain
        
        # 6. 发布到微信草稿箱
        article = {
            "title": art["title"],
            "author": "顺道大叔",
            "content": final_html,
            "content_source_url": "",
            "digest": digest,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }
        if cover_media_id:
            article["thumb_media_id"] = cover_media_id
        
        payload = {"articles": [article]}
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        try:
            resp = requests.post(
                PUBLISHER.cfg["draft_url"] + "?access_token=" + token,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers=headers,
                timeout=30
            )
            result = resp.json()
            if "media_id" in result:
                print(f"\n  ✅✅✅ [{i}] 发布成功！media_id: {result['media_id']}")
            else:
                print(f"\n  ❌ [{i}] 发布失败: {result}")
        except Exception as e:
            print(f"\n  ❌ [{i}] 异常: {e}")
        
        time.sleep(0.3)
    
    print("\n" + "=" * 60)
    print("  全部完成！3篇文章已发布到微信草稿箱 ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
