"""批量发布三篇觉知岛公众号文章（含品牌头图、封面图、配图）"""
import sys, os, re, time, json, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.publisher import WeChatPublisher

PUBLISHER = WeChatPublisher()
BASE = os.path.dirname(os.path.abspath(__file__))

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

def preprocess_markdown(md_text, inline_urls):
    """将文章中的图片标记替换为已上传的图片URL"""
    for i, url in enumerate(inline_urls):
        # 替换 ![配图：...](...) 格式
        md_text = re.sub(
            r'!\[.*?\]\(\.\/inline_.*?\.png\)',
            f'![配图{i+1}]({url})',
            md_text,
            count=1
        )
    # 替换品牌头图和封面图
    md_text = re.sub(
        r'!\[品牌头图\]\(\.\/brand_header\.png\)',
        '',
        md_text
    )
    return md_text

def main():
    token = PUBLISHER._get_access_token()
    if not token:
        print("❌ 获取 token 失败")
        return
    
    # 上传品牌头图（作为封面媒体文件备用）
    brand_path = os.path.join(BASE, "output/brand_header.png")
    brand_media_id = PUBLISHER._upload_image(token, brand_path, is_inline=True)
    print(f"📤 品牌头图URL: {brand_media_id[:50] if brand_media_id else 'None'}...")
    
    for i, art in enumerate(ARTICLES, 1):
        print(f"\n{'='*50}")
        print(f"📄 [{i}/3] 处理: {art['title']}")
        print(f"{'='*50}")
        
        # 1. 上传封面图
        cover_path = os.path.join(BASE, art["cover"])
        cover_media_id = PUBLISHER._upload_image(token, cover_path, is_inline=False)
        if not cover_media_id:
            print(f"❌ [{i}] 封面上传失败")
            continue
        print(f"   ✅ 封面上传成功")
        
        # 2. 上传所有配图
        inline_urls = []
        for inline_path in art["inline"]:
            full_path = os.path.join(BASE, inline_path)
            url = PUBLISHER._upload_image(token, full_path, is_inline=True)
            if url:
                inline_urls.append(url)
                print(f"   ✅ 配图上载: {os.path.basename(inline_path)}")
            else:
                inline_urls.append("")
                print(f"   ⚠️ 配图上载失败: {os.path.basename(inline_path)}")
        
        # 3. 读取文章
        file_path = os.path.join(BASE, art["file"])
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 4. 替换配图路径为已上传的URL
        processed = preprocess_markdown(content, inline_urls)
        
        # 5. 发布到微信草稿箱
        try:
            html, _ = PUBLISHER._markdown_to_html(processed, token)
            article_data = {
                "title": art["title"],
                "author": "顺道大叔",
                "content": html,
                "content_source_url": "",
                "digest": PUBLISHER._make_digest(content),
                "need_open_comment": 1,
                "only_fans_can_comment": 0,
                "thumb_media_id": cover_media_id,
            }
            
            payload = {"articles": [article_data]}
            headers = {"Content-Type": "application/json; charset=utf-8"}
            
            resp = requests.post(
                PUBLISHER.cfg["draft_url"] + "?access_token=" + token,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers=headers,
            )
            result = resp.json()
            if "media_id" in result:
                print(f"✅ [{i}] 发布成功！media_id: {result['media_id']}")
            else:
                print(f"❌ [{i}] 发布失败: {result}")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ [{i}] 发布异常: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
