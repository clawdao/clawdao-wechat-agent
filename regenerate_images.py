#!/usr/bin/env python3
"""
高质量封面&配图重生成脚本
- 使用 Seedream 3.0 生成独特背景
- 使用 PIL 叠加品牌文字（更精致）
- 封面 900×500，配图 640×400
- 生成 1:1 分享小图
"""
import sys, os, json, time, base64, io, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import load_config, get_seedream_config
from volcenginesdkcore.signv4 import SignerV4

# ====== 品牌常量 ======
BRAND_NAME = "觉知岛"
TAGLINE = "AI · 区块链 · 认知升级"
MOTTO = "知人者智，自知者明"
VALUES = "明道 · 取势 · 优术 · 利他"
ACCENT = (218, 185, 60)
ACCENT_LIGHT = (255, 220, 100)
TEXT_WHITE = (255, 255, 255)
TEXT_DIM = (200, 195, 190)
BG_DARK = (5, 8, 20)
OUTPUT_DIR = Path(__file__).parent / "output"

# ====== 字体 ======
def _font(size, bold=False):
    paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

# ====== Seedream API ======
class SeedreamHighQuality:
    """高质量图生成：优化提示词 + 精致文字叠加"""
    
    def __init__(self):
        cfg = get_seedream_config() or {}
        self.ak = cfg.get("access_key", "")
        self.sk = cfg.get("secret_key", "")
        self.endpoint = cfg.get("endpoint", "https://visual.volcengineapi.com")
        self.model = cfg.get("model", "high_aes_general_v30l_zt2i")
        self.enabled = cfg.get("enabled", False) and bool(self.ak) and bool(self.sk)
        self.region = "cn-north-1"
        self.service = "cv"
    
    def _call_api(self, action, body):
        if not self.enabled:
            raise RuntimeError("Seedream 未配置")
        query = {"Action": action, "Version": "2022-08-31"}
        body_str = json.dumps(body, ensure_ascii=False)
        headers = {
            "Content-Type": "application/json",
            "Host": "visual.volcengineapi.com",
        }
        SignerV4.sign("/", "POST", headers, body_str, {}, query,
                      self.ak, self.sk, self.region, self.service)
        from urllib.parse import urlencode
        url = f"{self.endpoint}?{urlencode(query)}"
        import urllib.request
        req = urllib.request.Request(url, data=body_str.encode("utf-8"), headers=headers, method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=120)
            return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            raise RuntimeError(f"API错误 ({e.code}): {raw[:300]}")
    
    def _submit_task(self, prompt, width, height):
        width, height = max(width, 512), max(height, 512)
        result = self._call_api("CVSync2AsyncSubmitTask", {
            "req_key": self.model,
            "prompt": prompt,
            "width": width, "height": height,
            "seed": -1, "scale": 2.5, "use_pre_llm": True,
        })
        if result.get("code") == 10000:
            return result["data"]["task_id"]
        raise RuntimeError(f"提交失败: [{result.get('code')}] {result.get('message','')}")
    
    def _query_task(self, task_id, max_retries=60, interval=2):
        body = {"req_key": self.model, "task_id": task_id}
        for i in range(max_retries):
            result = self._call_api("CVSync2AsyncGetResult", body)
            if result.get("code") != 10000:
                raise RuntimeError(f"查询失败: {result}")
            status = result["data"].get("status")
            if status == "done":
                data = result["data"]
                b64_list = data.get("binary_data_base64")
                if b64_list and len(b64_list) > 0:
                    return b64_list[0]
                urls = data.get("image_urls")
                if urls and len(urls) > 0:
                    return urls[0]
                raise RuntimeError(f"无图片数据")
            elif status in ("in_queue", "generating"):
                time.sleep(interval)
            else:
                raise RuntimeError(f"状态异常: {status}")
        raise TimeoutError(f"超时 ({max_retries*interval}s)")
    
    def generate_background(self, prompt, width, height):
        """生成背景图"""
        data = self._submit_task(prompt, width, height)
        img_data = self._query_task(data)
        if img_data.startswith("http"):
            import requests
            resp = requests.get(img_data, timeout=30)
            img = Image.open(io.BytesIO(resp.content))
        else:
            img = Image.open(io.BytesIO(base64.b64decode(img_data)))
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        return img.convert("RGB")
    
    # ====== 封面 ======
    def generate_cover(self, title):
        """高质量封面 900x500"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^\w\-]', '_', title[:25])
        path = OUTPUT_DIR / f"觉知岛_文章封面_900x500.png"
        
        # === 改进的 Seedream 提示词：更具体、更艺术 ===
        prompt = (
            "Elegant zen digital art, abstract software evolution visualization, "
            "project-based paradigm shift, floating luminous software modules transforming into organic living structures, "
            "golden data streams flowing upward, deep navy to charcoal gradient background, "
            "subtle grid lines fading into infinity, particles of light, "
            "minimalist composition with golden ratio balance, "
            "cinematic lighting, 8k resolution, premium tech magazine aesthetic, "
            "oriental ink wash meets digital neon, ethereal atmosphere. "
            "NO text, NO letters, NO characters, NO typography. Pure background art."
        )
        
        print(f"  🎨 生成封面背景 (900x500)...")
        bg = self.generate_background(prompt, 900, 500)
        draw = ImageDraw.Draw(bg, "RGBA")
        
        # 半透明遮罩（改善文字可读性）
        overlay = Image.new("RGBA", (900, 500), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        # 中心渐变遮罩
        for y in range(500):
            alpha = int(30 * (1 - abs(y - 250) / 250))
            overlay_draw.line([(0, y), (900, y)], fill=(0, 0, 0, alpha))
        bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(bg, "RGBA")
        
        # === 绘制封面文字（安全区 200~700）===
        SAFE_LEFT, SAFE_RIGHT = 200, 700
        SAFE_CX = 450
        
        # 品牌名 + 装饰线
        brand_font = _font(16, True)
        brand_text = f"◆ {BRAND_NAME}"
        bw = brand_font.getbbox(brand_text)[2]
        draw.text((SAFE_CX - bw//2, 30), brand_text, fill=(*ACCENT, 240), font=brand_font)
        draw.line([(SAFE_CX-22, 54), (SAFE_CX+22, 54)], fill=(*ACCENT, 140), width=1)
        
        # 标题（自动折行，居中安全区）
        safe_w = 460  # 可用宽度
        f_title = _font(36, True)
        lines, cur = [], ""
        for ch in title:
            test = cur + ch
            if f_title.getbbox(test)[2] > safe_w:
                lines.append(cur); cur = ch
            else:
                cur = test
        if cur: lines.append(cur)
        if not lines: lines = ["好文"]
        if len(lines) > 2:
            f_title = _font(28, True)
            lines = lines[:2]
            if len(lines[1]) > 18: lines[1] = lines[1][:17] + "…"
        
        lh = f_title.getbbox("测")[3] + 12
        total_h = len(lines) * lh + 8
        sy = (500 - total_h) // 2 - 30
        
        for i, line in enumerate(lines):
            y_pos = sy + i * lh
            line_w = f_title.getbbox(line)[2]
            lx = SAFE_CX - line_w // 2
            # 阴影 + 主文字
            draw.text((lx+2, y_pos+2), line, fill=(0,0,0,100), font=f_title)
            draw.text((lx, y_pos), line, fill=(*TEXT_WHITE, 250), font=f_title)
        
        # 金句
        motto_font = _font(14)
        motto_text = f"「 {MOTTO} 」"
        mw = motto_font.getbbox(motto_text)[2]
        my = sy + total_h + 35
        draw.text((SAFE_CX - mw//2, my), motto_text, fill=(*ACCENT, 215), font=motto_font)
        
        # 分隔线
        sep_y = my + 28
        draw.line([(SAFE_CX-22, sep_y), (SAFE_CX+22, sep_y)], fill=(*ACCENT, 140), width=1)
        draw.line([(SAFE_CX-16, sep_y+3), (SAFE_CX+16, sep_y+3)], fill=(*ACCENT, 50), width=1)
        
        # 价值观
        vf = _font(13)
        vw = vf.getbbox(VALUES)[2]
        draw.text((SAFE_CX - vw//2, sep_y+14), VALUES, fill=(*ACCENT, 175), font=vf)
        
        # 底部tag
        tf = _font(13)
        tw = tf.getbbox(TAGLINE)[2]
        draw.text((SAFE_CX - tw//2, 500-28), TAGLINE, fill=(*TEXT_DIM, 190), font=tf)
        
        bg.save(path, "PNG", optimize=True)
        size_kb = path.stat().st_size / 1024
        print(f"  ✅ 封面已保存: {path} ({size_kb:.0f} KB)")
        return path
    
    # ====== 配图 ======
    def generate_inline(self, title, prompt_extra, style, index=1):
        """生成配图 640x400"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^\w\-]', '_', title[:20])
        path = OUTPUT_DIR / f"inline_{safe_name}_{style}.png"
        
        # Seedream 背景提示词
        base_prompts = {
            "steps": (
                "Abstract progressive flow visualization, sequential stages connected by luminous golden paths, "
                "3 ascending levels with directional arrows, digital evolution timeline concept, "
                "deep blue to warm gold gradient, particles along the path, "
                "minimalist elegant data visualization style, premium tech magazine infographic feel"
            ),
            "concept": (
                "Radial concept visualization, central luminous sphere radiating golden threads to surrounding nodes, "
                "knowledge graph aesthetic, interconnected network of ideas, "
                "deep space dark blue background with subtle star particles, "
                "tech ecosystem diagram style, premium infographic quality"
            ),
            "quote": (
                "Elegant zen negative space, warm soft golden glow emanating from center, "
                "minimalist composition with vast empty space, subtle atmospheric light rays, "
                "deep charcoal to navy gradient, peaceful contemplative mood, "
                "premium literary quote background, high-end texture paper feel"
            ),
        }
        base = base_prompts.get(style, base_prompts["concept"])
        prompt = f"{base}, {prompt_extra}, NO text, NO letters. Pure background."
        
        print(f"  🎨 生成配图 [{index}] ({style}): {title}")
        bg = self.generate_background(prompt, 640, 400)
        draw = ImageDraw.Draw(bg, "RGBA")
        
        # 半透明遮罩（增强可读性）
        overlay = Image.new("RGBA", (640, 400), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([(0, 0), (640, 60)], fill=(0, 0, 0, 80))
        overlay_draw.rectangle([(0, 340), (640, 400)], fill=(0, 0, 0, 80))
        bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(bg, "RGBA")
        
        # 左上角标
        draw.text((16, 12), "◆", fill=(*ACCENT, 150), font=_font(14))
        
        if style == "steps":
            # 步骤图
            draw.text((30, 20), "演进路线", fill=(*ACCENT, 200), font=_font(14))
            steps = ["1.0 买断制", "2.0 订阅制", "3.0 项目制"]
            fs = _font(20)
            for i, s in enumerate(steps):
                y = 70 + i * 90
                # 圆圈
                r = 14
                draw.ellipse([40 - r, y - r, 40 + r, y + r], outline=(*ACCENT, 200), width=2)
                draw.text((40 - 5, y - 7), str(i+1), fill=(*ACCENT, 220), font=_font(16, True))
                draw.text((64, y - 8), s, fill=(*TEXT_WHITE, 230), font=fs)
                # 箭头
                if i < 2:
                    draw.text((40 - 4, y + 32), "↓", fill=(*ACCENT, 120), font=_font(20))
                    # 连接线
                    draw.line([(40, y + r + 5), (40, y + 90 - r - 5)], fill=(*ACCENT, 60), width=1)
            # 底部说明
            draw.text((30, 370), "用户主权回归 → 控制权递增", fill=(*ACCENT, 150), font=_font(12))
            
        elif style == "concept":
            # 概念图
            draw.text((30, 20), "核心特征", fill=(*ACCENT, 200), font=_font(14))
            concepts = [
                ("可配置", "从空白开始，由你定义"),
                ("可进化", "积累对话，越用越强"),
                ("可组合", "多项目协作，能力网络"),
                ("可继承", "可导出分享，代际传递"),
            ]
            for i, (name, desc) in enumerate(concepts):
                cx = 80 + (i % 2) * 260
                cy = 90 + (i // 2) * 120
                # 圆角矩形标签
                tw, th = 230, 80
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        draw.rounded_rectangle([cx+dx, cy+dy, cx+tw+dx, cy+th+dy], radius=10,
                                              fill=(*ACCENT, 15 if abs(dx)<=1 and abs(dy)<=1 else 5), outline=None)
                draw.rounded_rectangle([cx, cy, cx+tw, cy+th], radius=10,
                                      fill=(*ACCENT, 20), outline=(*ACCENT, 40), width=1)
                # 标题
                draw.text((cx + 15, cy + 12), name, fill=(*ACCENT, 220), font=_font(18, True))
                # 说明
                draw.text((cx + 15, cy + 44), desc, fill=(*TEXT_WHITE, 180), font=_font(13))
                # 角标序号
                draw.text((cx + tw - 25, cy + 12), f"0{i+1}", fill=(*ACCENT, 80), font=_font(12))
            
        elif style == "quote":
            # 金句图 - 大号引用
            draw.text((30, 25), "“", fill=(*ACCENT, 100), font=_font(60))
            quote = "代码是死的，项目是活的"
            subtitle = "—— 因为项目里有对话、有知识库、有持续的进化"
            fq = _font(24, True)
            # 自动折行
            qlines, cur = [], ""
            for ch in quote:
                test = cur + ch
                if fq.getbbox(test)[2] > 540:
                    qlines.append(cur); cur = ch
                else:
                    cur = test
            if cur: qlines.append(cur)
            
            for i, line in enumerate(qlines):
                draw.text((50, 90 + i * 38), line, fill=(*TEXT_WHITE, 240), font=fq)
            
            draw.text((50, 90 + len(qlines) * 38 + 10), subtitle, fill=(*TEXT_DIM, 180), font=_font(14))
            draw.text((560, 360), "”", fill=(*ACCENT, 100), font=_font(60))
        
        bg.save(path, "PNG", optimize=True)
        size_kb = path.stat().st_size / 1024
        print(f"  ✅ 配图已保存: {path} ({size_kb:.0f} KB)")
        return path
    
    # ====== 分享小图 ======
    def generate_share_square(self, cover_path):
        """从封面裁剪 1:1 中心分享图"""
        out_path = OUTPUT_DIR / "觉知岛_分享小图_500x500.png"
        img = Image.open(cover_path)
        # 宽900高500，中心500x500 = crop(200, 0, 700, 500)
        square = img.crop((200, 0, 700, 500))
        square.save(out_path, "PNG", optimize=True)
        size_kb = out_path.stat().st_size / 1024
        print(f"  ✅ 分享小图已保存: {out_path} ({size_kb:.0f} KB)")
        return out_path


# ====== 更新文章 ======
ARTICLE_PATH = Path(__file__).parent / "output" / "05-从用软件到长软件_配图版.md"

def update_article(inline_paths):
    """将配图占位符替换为实际图片路径"""
    if not ARTICLE_PATH.exists():
        print(f"  ❌ 文章不存在: {ARTICLE_PATH}")
        return None
    
    text = ARTICLE_PATH.read_text(encoding="utf-8")
    
    # 替换配图路径
    replacements = {
        "软件交付三次革命": inline_paths.get("steps", ""),
        "长软件四个核心特征": inline_paths.get("concept", ""),
        "代码是死的，项目是活的": inline_paths.get("quote", ""),
    }
    
    for key, path in replacements.items():
        if path:
            old = f"./inline_{key.replace(' ', '_')}"
            new = f"./{path.name}"
            text = text.replace(old, new)
            text = text.replace(key.replace(' ', '_'), path.stem)
    
    # 写回
    ARTICLE_PATH.write_text(text, encoding="utf-8")
    print(f"  ✅ 文章已更新: {ARTICLE_PATH}")
    return ARTICLE_PATH


# ====== 主流程 ======
def main():
    print("=" * 55)
    print("  🌟 觉知岛 · 高质量图像重生成")
    print("=" * 55)
    
    sg = SeedreamHighQuality()
    if not sg.enabled:
        print("\n  ❌ Seedream 未启用，请检查 config.json 配置")
        sys.exit(1)
    
    print(f"\n  模型: {sg.model}")
    print(f"  AK: {sg.ak[:8]}...")
    
    # 1. 生成封面
    print(f"\n{'─'*50}")
    print("  📋 步骤 1/4: 生成封面图 (900×500)")
    print(f"{'─'*50}")
    cover = sg.generate_cover("从「用软件」到「长软件」")
    
    # 2. 生成内文配图
    print(f"\n{'─'*50}")
    print("  📋 步骤 2/4: 生成内文配图")
    print(f"{'─'*50}")
    
    inline_paths = {}
    
    print("\n  [配图 1/3] 软件交付三次革命 - 步骤图")
    inline_paths["steps"] = sg.generate_inline(
        "软件交付三次革命",
        "tech evolution timeline, three ascending stages, software delivery revolution, golden connection lines, progress visualization",
        "steps", 1
    )
    
    print("\n  [配图 2/3] 长软件四个核心特征 - 概念图")  
    inline_paths["concept"] = sg.generate_inline(
        "长软件四个核心特征",
        "four interconnected nodes forming a diamond pattern, software ecosystem, organic growth concept, knowledge network visualization",
        "concept", 2
    )
    
    print("\n  [配图 3/3] 代码是死的，项目是活的 - 金句图")
    inline_paths["quote"] = sg.generate_inline(
        "代码是死的，项目是活的",
        "zen contemplative space, warm soft golden glow, vast empty elegance, peaceful atmosphere, premium literary mood, dark charcoal gradient",
        "quote", 3
    )
    
    # 3. 生成分享小图
    print(f"\n{'─'*50}")
    print("  📋 步骤 3/4: 生成分享小图 (500×500)")
    print(f"{'─'*50}")
    share = sg.generate_share_square(cover)
    
    # 4. 更新文章
    print(f"\n{'─'*50}")
    print("  📋 步骤 4/4: 更新文章配图路径")
    print(f"{'─'*50}")
    result = update_article(inline_paths)
    
    print(f"\n{'='*55}")
    print("  ✅ 全部完成!")
    print(f"{'='*55}")
    print(f"\n  封面: {cover}")
    print(f"  分享小图: {share}")
    for k, v in inline_paths.items():
        print(f"  配图[{k}]: {v}")
    if result:
        print(f"  文章: {result}")

if __name__ == "__main__":
    main()
