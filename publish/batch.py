"""批量发布三篇觉知岛公众号文章到微信草稿箱"""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.publisher import WeChatPublisher

PUBLISHER = WeChatPublisher()

# 现有的封面图（任选一张作为通用封面）
COVER_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           "output/cover_顺道而为_认知升级_人生选择.png")

ARTICLES = [
    {
        "file": "output/article_觉知系统_01.md",
        "title": "越焦虑的人 越需要一个觉知系统",
    },
    {
        "file": "output/article_认知框架_02.md",
        "title": "你的大脑还在用2G网 换这套认知框架试试",
    },
    {
        "file": "output/article_智能体战队_03.md",
        "title": "一个人干翻一个团队 秘密是这3个智能体",
    },
]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 先获取 token
    token = PUBLISHER._get_access_token()
    if not token:
        print("❌ 获取 token 失败")
        return
    
    # 上传封面图
    print("📤 上传封面图...")
    cover_media_id = PUBLISHER._upload_image(token, COVER_IMAGE, is_inline=False)
    if not cover_media_id:
        print("❌ 封面上传失败，尝试用临时图片生成")
        # 用已有的一张图
        cover_media_id = PUBLISHER._upload_image(
            token, 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "output/cover_副业不是第二份工作_而是你的另一种可能.png"),
            is_inline=False
        )
    print(f"📤 封面 media_id: {cover_media_id}")
    
    if not cover_media_id:
        print("❌ 无法获取封面 media_id，终止发布")
        return
    
    for i, art in enumerate(ARTICLES, 1):
        file_path = os.path.join(base_dir, art["file"])
        if not os.path.exists(file_path):
            print(f"❌ [{i}] 文件不存在: {file_path}")
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"\n{'='*50}")
        print(f"📄 [{i}/3] 发布: {art['title']}")
        print(f"{'='*50}")
        
        try:
            html, _ = PUBLISHER._markdown_to_html(content, token)
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
            
            import requests, json
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
            
            # 稍微延迟避免频率限制
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ [{i}] 发布异常: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
