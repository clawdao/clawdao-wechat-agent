#!/usr/bin/env python3
"""
觉知岛 · 公众号发布脚本 v3

结构：
  [品牌头图] ← brand_header.png（统一品牌宣传）
  [标题背景框] ← title_banner_xxx.png（带标题的独立背景图）
  正文（含文中插图至少1张）

封面通过 thumb_media_id 独立上传，不出现在正文中。
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
    },
    {
        "file": "output/article_final_02.md",
        "title": "你的大脑还在用2G网 换这套认知框架试试",
        "cover": "output/cover_你的大脑还在用2G网_换这套认知框架试试.png",
    },
    {
        "file": "output/article_final_03.md",
        "title": "一个人干翻一个团队 秘密是这3个智能体",
        "cover": "output/cover_一个人干翻一个团队_秘密是这3个智能体.png",
    },
]


def upload_image(token, path, is_inline=False):
    """上传图片并返回media_id或url"""
    try:
        if not os.path.exists(path):
            print(f"  ⚠️ 文件不存在: {path}")
            return None
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


def main():
    print("=" * 60)
    print("  觉知岛 · 公众号发布 v3")
    print("  3篇爆款文章")
    print("  品牌头图 + 标题背景框 + 文中插图 + 独立封面")
    print("=" * 60)
    
    # 获取token
    token = PUBLISHER._get_access_token()
    if not token:
        print("❌ 无法获取微信access token，请检查配置")
        return
    
    # 上传品牌头图（统一品牌宣传图，放在文章最顶部）
    print("\n📤 上传统一品牌头图...")
    brand_path = os.path.join(OUT, "brand_header.png")
    brand_url = upload_image(token, brand_path, is_inline=True)
    if brand_url:
        print(f"  ✅ 品牌头图上载成功")
    else:
        print(f"  ⚠️ 品牌头图上传失败")
    
    # 逐篇处理
    for i, art in enumerate(ARTICLES, 1):
        print(f"\n{'='*50}")
        print(f"📄 [{i}/3] {art['title']}")
        print(f"{'='*50}")
        
        # 1. 上传封面图（作为 thumb_media_id，不出现在正文中）
        cover_path = os.path.join(BASE, art["cover"])
        cover_media_id = upload_image(token, cover_path, is_inline=False)
        if cover_media_id:
            print(f"  ✅ 封面上载成功")
        else:
            print(f"  ⚠️ 封面失败，继续发布")
        
        # 2. 读取文章markdown
        file_path = os.path.join(BASE, art["file"])
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        # 3. 调用 markdown → HTML（会自动上传所有 ![xxx](./xxx.png) 图片）
        html_body, _ = PUBLISHER._markdown_to_html(md_content, token)
        
        # 4. 构建最终HTML：品牌头图 + 正文
        brand_section = (
            f'<section style="margin: 0 0 5px 0; text-align: center;">'
            f'<img src="{brand_url}" alt="觉知岛" style="width: 100%; max-width: 100%; border-radius: 12px;" />'
            f'</section>'
        )
        
        final_html = f'<section style="padding: 0 5px;">\n{brand_section}\n{html_body}\n</section>'
        
        # 5. 生成摘要
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
