"""微信公众平台发布模块 - 精排版 + 64字标题 + 作者顺道大叔"""
import re
import time
import os
import json
import requests
from config import get_wechat_config


class WeChatPublisher:
    """微信公众平台草稿箱发布器"""


    @staticmethod
    def _make_keywords(title: str, md_content: str) -> str:
        """从文章标题和内容中提取关键词（用于GEO）"""
        stop_words = {"一个", "可以", "这个", "那个", "什么", "怎么", "如何", "没有",
                      "不是", "就是", "我们", "他们", "你们", "自己", "已经",
                      "还是", "因为", "所以", "但是", "而且", "如果", "虽然"}
        text = title + " " + md_content[:500]
        text = re.sub(r"[#>*\[\]`]", "", text)

        words = re.findall(r'[一-鿿]{2,8}', text)
        freq = {}
        for w in words:
            if w not in stop_words:
                freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: -x[1])
        top = [w for w, _ in sorted_words[:12] if len(w) >= 2]
        return "、".join(top) if top else ""

    @staticmethod
    def _build_jsonld(title: str, digest: str, keywords: str) -> str:
        """构建Article JSON-LD结构化数据（GEO核心）"""
        today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        ld = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": digest,
            "author": {
                "@type": "Person",
                "name": "顺道大叔"
            },
            "publisher": {
                "@type": "Organization",
                "name": "觉知岛",
                "description": "东方智慧 + 现代科技，AI时代的认知升级平台"
            },
            "datePublished": today,
        }
        if keywords:
            ld["keywords"] = keywords
        return json.dumps(ld, ensure_ascii=False)

    def __init__(self):
        self.cfg = get_wechat_config()
        self.access_token = None
        self.token_expires = 0

    def _get_access_token(self) -> str:
        now = time.time()
        if self.access_token and now < self.token_expires - 60:
            return self.access_token
        if not self.cfg["appid"] or not self.cfg["appsecret"]:
            print("⚠️  未配置微信公众平台 appid/appsecret")
            return None
        resp = requests.get(self.cfg["token_url"], params={
            "grant_type": "client_credential",
            "appid": self.cfg["appid"],
            "secret": self.cfg["appsecret"],
        })
        data = resp.json()
        if "access_token" in data:
            self.access_token = data["access_token"]
            self.token_expires = now + data.get("expires_in", 7200)
            return self.access_token
        else:
            print(f"❌ 获取 access_token 失败: {data}")
            return None

    def _make_digest(self, md_content: str) -> str:
        """生成摘要：取文章前80字纯文本"""
        plain = re.sub(r"[#>*\[\]`\n]", "", md_content).strip()
        plain = re.sub(r"\s+", " ", plain)
        if len(plain) > 80:
            plain = plain[:80] + "…"
        return plain

    def save_as_draft(self, title: str, content: str, cover_image_path: str = None) -> bool:
        # 清理标题特殊字符，但保留长度（微信支持64字）
        for ch in ['"', '"', "'", "'"]:
            title = title.replace(ch, '')
        # 微信标题上限约64字
        if len(title) > 64:
            title = title[:64]

        token = self._get_access_token()
        if not token:
            return False

        html, inline_media_ids = self._markdown_to_html(content, token)

        # 上传品牌头图并置顶（统一品牌宣传图，放在文章最上方）
        brand_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "brand_header.png")
        if os.path.exists(brand_path):
            brand_url = self._upload_image(token, brand_path, is_inline=True)
            if brand_url:
                brand_html = (
                    f'<section style="margin: 0 0 12px 0; text-align: center;">'
                    f'<img src="{brand_url}" alt="觉知岛" style="width: 100%; max-width: 100%; border-radius: 12px;" />'
                    f'</section>'
                )
                html = brand_html + html
        else:
            print(f"  ℹ️ 品牌头图不存在（跳过）: {brand_path}")

        # GEO：注入JSON-LD结构化数据（帮助AI理解文章内容）
        keywords = self._make_keywords(title, content)
        jsonld = self._build_jsonld(title, self._make_digest(content), keywords)
        jsonld_script = (
            f'<script type="application/ld+json">'
            f'{jsonld}'
            f'</script>'
        )
        # 用语义化<article>包裹全文 + JSON-LD放在开头（AI可见但用户不可见）
        html = f'<article>{jsonld_script}{html}</article>'

        media_id = None
        if cover_image_path:
            media_id = self._upload_image(token, cover_image_path)

        article = {
            "title": title,
            "author": "顺道大叔",
            "content": html,
            "content_source_url": "",
            "digest": self._make_digest(content),
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }
        if media_id:
            article["thumb_media_id"] = media_id

        # 如果有文章中插入的图片，加到文章数据里

        payload = {"articles": [article]}

        headers = {"Content-Type": "application/json; charset=utf-8"}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        resp = requests.post(
            self.cfg["draft_url"] + "?access_token=" + token,
            data=body,
            headers=headers,
        )
        result = resp.json()
        if "media_id" in result:
            print(f"✅ 文章已保存到公众号草稿箱！media_id: {result['media_id']}")
            return True
        else:
            print(f"❌ 保存草稿失败: {result}")
            return False

    def _upload_image(self, token, path, is_inline=False):
        """上传图片，返回media_id"""
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
                    print(f"⚠️  上传图片失败: {data}")
                    return None
        except Exception as e:
            print(f"❌ 上传图片异常: {e}")
            return None

    def _markdown_to_html(self, md: str, token=None) -> tuple:
        """Markdown → 精美微信图文HTML（模仿参考文章排版）

        参考文章风格：
        - 大标题渐变背景 + 白色文字
        - 小标题左侧彩色竖条 + 浅色背景
        - 金句引用用彩色左侧竖条 + 浅底色
        - 正文留白舒适，字号15px，行高1.9
        - 重要文字用彩色突出
        - 文中可嵌入图片
        - 分隔符用精致的圆点或装饰线
        """
        lines = md.split("\n")
        parts = []

        # 品牌色
        C_PRIMARY = "#1a1a2e"     # 深蓝黑
        C_ACCENT = "#c8a84e"      # 觉知岛金色
        C_GOLD = "#b8963e"        # 深金
        C_ACCENT_LIGHT = "#f5f0e8"  # 金色浅底
        C_BG_GOLD = "linear-gradient(135deg, #c8a84e 0%, #a07d30 100%)"

        first_title = None
        for line in lines:
            if line.startswith("# ") and not line.startswith("## "):
                first_title = line[2:].strip()
                break

        # === 标题区（精简版：纯文字 + 金色底线装饰）===
        if first_title:
            parts.append(
                f'<section style="margin: 0 0 20px 0; text-align: center;">'
                f'<h1 style="font-size: 18px; font-weight: 700; color: {C_PRIMARY}; margin: 0; line-height: 1.6; letter-spacing: 0.5px;">'
                f'{first_title}</h1>'
                f'<section style="width: 36px; height: 3px; background: {C_ACCENT}; margin: 10px auto 0 auto; border-radius: 2px;"></section>'
                f'</section>'
            )

        # === 文章正文 ===
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                parts.append('<p style="margin: 10px 0;">&nbsp;</p>')
            elif line.startswith("# ") and not line.startswith("## "):
                continue
            elif line.startswith("## "):
                sub = line[3:]
                parts.append(
                    f'<section style="margin: 28px 0 14px 0;">'
                    f'<section style="display: flex; align-items: center;">'
                    f'<section style="width: 4px; height: 20px; background: {C_ACCENT}; border-radius: 2px; margin-right: 10px;"></section>'
                    f'<h3 style="font-size: 17px; font-weight: 700; margin: 0; color: {C_PRIMARY}; line-height: 1.5;">{sub}</h3>'
                    f'</section></section>'
                )
            elif line.startswith("> "):
                quote = line[2:]
                parts.append(
                    f'<section style="background: {C_ACCENT_LIGHT}; border-left: 4px solid {C_ACCENT};'
                    f'margin: 16px 0; padding: 14px 18px; border-radius: 0 8px 8px 0;">'
                    f'<p style="margin: 0; font-size: 14px; line-height: 1.8; color: #6b5b3e; font-style: normal;">{quote}</p>'
                    f'</section>'
                )
            elif line.startswith("---"):
                parts.append(
                    f'<section style="margin: 28px 0; text-align: center; color: {C_ACCENT}; font-size: 14px; letter-spacing: 6px;">✦ ✦ ✦</section>'
                )
            elif line.startswith("![") and "](" in line and line.rstrip().endswith(")"):
                # 图片标记 ![alt](path)
                alt = line[2:line.index("]")]
                path = line[line.index("(")+1:-1]
                if token:
                    import os
                    # 支持 ./xxx.png 或 output/xxx.png 两种路径
                    if path.startswith("./"):
                        # 从当前工作目录或 output 目录寻找
                        script_dir = os.path.dirname(os.path.abspath(__file__))  # core/
                        project_dir = os.path.dirname(script_dir)               # 项目根
                        cwd_path = os.path.join(os.getcwd(), path[2:])
                        # 优先检查项目 outputs 目录（实际文件所在位置）
                        out_path = os.path.join(project_dir, "outputs", path[2:])
                        # 也检查项目 output 目录作为备用
                        legacy_out = os.path.join(project_dir, "output", path[2:])
                        # 也检查 script_dir/output 作为兜底（旧版兼容）
                        script_out = os.path.join(script_dir, "output", path[2:])
                        # 也检查原始位置
                        old_path = f"/Users/imfly/Documents/公众号/output/{path[2:]}"
                        for candidate in (out_path, legacy_out, script_out, cwd_path, old_path):
                            if os.path.exists(candidate):
                                full_path = candidate
                                break
                        else:
                            full_path = out_path  # 最后尝试，让 _upload_image 报错提示
                    elif path.startswith("output/"):
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        full_path = os.path.join(script_dir, path)
                    else:
                        full_path = path
                    url = self._upload_image(token, full_path, is_inline=True)
                    if url:
                        parts.append(
                            f'<section style="margin: 20px 0; text-align: center;">'
                            f'<img src="{url}" alt="{alt}" style="width: 100%; max-width: 100%; border-radius: 10px;" />'
                            f'</section>'
                        )
                    else:
                        parts.append(f'<p style="margin: 10px 0; font-size: 14px; color: #999;">[图片: {alt}]</p>')
                else:
                    parts.append(f'<p style="margin: 10px 0; font-size: 14px; color: #999;">[图片: {alt}]</p>')
            elif line.startswith("**") and line.endswith("**"):
                bold = line.strip("*")
                parts.append(
                    f'<p style="margin: 10px 0; font-weight: 700; color: {C_ACCENT}; font-size: 15px; line-height: 1.9;">{bold}</p>'
                )
            elif line.startswith("### "):
                sub = line[4:]
                parts.append(
                    f'<section style="margin: 22px 0 10px 0;">'
                    f'<h4 style="font-size: 15px; font-weight: 700; margin: 0; color: {C_PRIMARY};">▎ {sub}</h4>'
                    f'</section>'
                )
            else:
                # 普通段落：处理行内加粗
                text = line
                # 将 **加粗** 转为内联html
                text = re.sub(r'\*\*(.+?)\*\*', rf'<strong style="color: {C_ACCENT};">\1</strong>', text)
                parts.append(
                    f'<p style="margin: 8px 0; font-size: 15px; line-height: 1.9; color: #333; letter-spacing: 0.5px;">{text}</p>'
                )

        return ("\n".join(parts), [])

    def _generate_inline_image(self, topic, token):
        """根据主题生成一张文中插图并上传，返回URL"""
        try:
            # 直接用封面生成器生成一张方形图作为文中插图
            from cover_generator import generate_cover
            import os
            out_dir = os.path.join(os.path.dirname(__file__), 'output')
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, "inline_img.png")
            # 生成一张900x400的插图
            from config import get_cover_config
            cfg = get_cover_config()
            from PIL import Image, ImageDraw, ImageFont
            from pathlib import Path

            W, H = 900, 400
            img = Image.new("RGBA", (W, H), (10, 12, 20))
            draw = ImageDraw.Draw(img)

            # 渐变背景
            for y in range(H):
                r = int(10 + (18 - 10) * y / H)
                g = int(12 + (20 - 12) * y / H)
                b = int(20 + (30 - 20) * y / H)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # 金色装饰线
            accent = (200, 170, 60)
            draw.line([(40, 180), (W - 40, 180)], fill=(*accent, 40), width=1)
            draw.line([(40, 220), (W - 40, 220)], fill=(*accent, 20), width=1)

            # 中央文字
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
            ]
            ft = None
            for p in font_paths:
                if Path(p).exists():
                    ft = ImageFont.truetype(p, 28)
                    break
            if ft:
                draw.text((W//2 - 140, 140), "◆ 觉知岛", fill=(*accent, 180), font=ft)
                ft2 = ImageFont.truetype(font_paths[0] if Path(font_paths[0]).exists() else font_paths[1], 20)
                draw.text((W//2 - 160, 250), "一人组织 · AI 驱动 · 顺道而为", fill=(*accent, 100), font=ft2)

            # 装饰星点
            import random
            random.seed(hash(topic))
            for _ in range(20):
                x = random.randint(50, W - 50)
                y = random.randint(30, H - 30)
                draw.ellipse([x-1, y-1, x+1, y+1], fill=(*accent, random.randint(10, 30)))

            img.convert("RGB").save(path, "PNG", optimize=True)
            url = self._upload_image(token, path, is_inline=True)
            return url
        except Exception as e:
            print(f"⚠️  生成文中插图失败: {e}")
            return None
