"""
Seedream文生图 + PIL文字叠加混合引擎
火山引擎 Seedream 3.0 生成独特背景 + PIL 叠加品牌文字
保留现有 PIL 生图作为默认，本模块作为增强选项
"""

import json
import time
import base64
import io
import re
import os
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
from volcenginesdkcore.signv4 import SignerV4


# ====== 品牌常量（与 cover_generator.py 一致） ======
BRAND_NAME = "觉知岛"
TAGLINE = "AI · 区块链 · 认知升级"
MOTTO = "知人者智，自知者明"
VALUES = "明道 · 取势 · 优术 · 利他"

ACCENT = (218, 185, 60)        # 金色
ACCENT_LIGHT = (255, 220, 100)  # 亮金
TEXT_WHITE = (255, 255, 255)
TEXT_DIM = (200, 195, 190)
BG_DARK = (5, 8, 20)

OUTPUT_DIR = Path(__file__).parent / "output"


# ====== 字体工具 ======
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _blend_color(c1, c2, ratio):
    return tuple(int(a + (b - a) * ratio) for a, b in zip(c1, c2))


# ====== Seedream API 客户端 ======
class SeedreamGenerator:
    """Seedream 文生图 + PIL 文字叠加混合引擎"""

    def __init__(self, config: dict = None):
        if config is None:
            from config import load_config
            cfg = load_config()
            config = cfg.get("seedream", {})
            if not config:
                from config import get_seedream_config
                config = get_seedream_config()

        self.ak = config.get("access_key", "")
        raw_sk = config.get("secret_key", "")
        # 重要：Volcengine SecretKey 是原始字符串，不需要 base64 解码
        self.sk = raw_sk
        self.endpoint = config.get("endpoint",
                                    "https://visual.volcengineapi.com")
        self.model = config.get("model", "high_aes_general_v30l_zt2i")
        self.enabled = config.get("enabled", False) and bool(self.ak) and bool(self.sk)
        self.region = "cn-north-1"
        self.service = "cv"

    # ---- API 底层 ----

    def _call_api(self, action: str, body: dict) -> dict:
        """使用原生 Volcengine SDK V4 签名调用 Seedream API"""
        if not self.enabled:
            raise RuntimeError("Seedream 未配置（请在 config.json 设置 access_key/secret_key）")

        query = {"Action": action, "Version": "2022-08-31"}
        body_str = json.dumps(body, ensure_ascii=False)
        url_path = "/"
        method = "POST"
        headers = {
            "Content-Type": "application/json",
            "Host": "visual.volcengineapi.com",
        }

        # 使用原生 Volcengine V4 签名（直接修改 headers 添加 X-Date/X-Content-Sha256/Authorization）
        SignerV4.sign(url_path, method, headers, body_str, {}, query,
                      self.ak, self.sk, self.region, self.service)

        from urllib.parse import urlencode
        url = f"{self.endpoint}?{urlencode(query)}"

        # 使用 urllib（requests 库与 SignerV4 兼容性有问题）
        import urllib.request
        req = urllib.request.Request(url, data=body_str.encode("utf-8"),
                                      headers=headers, method=method)
        try:
            resp = urllib.request.urlopen(req, timeout=60)
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            raise RuntimeError(f"Seedream API 错误 ({e.code}): {raw[:300]}")

    def _submit_task(self, prompt: str, width: int, height: int) -> str:
        # 确保最小尺寸满足模型要求（至少 512x512）
        width = max(width, 512)
        height = max(height, 512)
        result = self._call_api("CVSync2AsyncSubmitTask", {
            "req_key": self.model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "seed": -1,
            "scale": 2.5,
            "use_pre_llm": True,
        })
        if result.get("code") == 10000:
            return result["data"]["task_id"]
        msg = result.get("message", "未知错误")
        raise RuntimeError(f"提交Seedream任务失败: [{result.get('code')}] {msg}")

    def _query_task(self, task_id: str, max_retries: int = 60,
                    interval: int = 2) -> str:
        """轮询任务结果，返回 base64 编码的图片数据"""
        body = {"req_key": self.model, "task_id": task_id}
        for i in range(max_retries):
            result = self._call_api("CVSync2AsyncGetResult", body)
            if result.get("code") != 10000:
                raise RuntimeError(f"查询任务失败: {result}")

            status = result["data"].get("status", "")
            if status == "done":
                b64_list = result["data"].get("binary_data_base64")
                if b64_list and len(b64_list) > 0:
                    return b64_list[0]
                urls = result["data"].get("image_urls")
                if urls and len(urls) > 0:
                    return urls[0]
                raise RuntimeError(f"无图片数据: {result}")
            elif status in ("in_queue", "generating"):
                time.sleep(interval)
            else:
                raise RuntimeError(f"任务状态异常: status={status}")
        raise TimeoutError(f"Seedream 任务超时（{max_retries * interval}s）")

    def generate_background(self, prompt: str, width: int = 900,
                            height: int = 383) -> Image.Image:
        """用 Seedream 生成背景图，返回 PIL Image"""
        task_id = self._submit_task(prompt, width, height)
        image_data = self._query_task(task_id)

        if image_data.startswith("http"):
            resp = requests.get(image_data, timeout=30)
            img = Image.open(io.BytesIO(resp.content))
        else:
            img_data = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_data))

        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        return img.convert("RGB")

    # ---- Prompt 构建 ----

    def _prompt_cover(self, topic: str = "", keywords: list = None) -> str:
        """根据文章主题生成封面背景创意
        每次按文章内容生成独特的视觉风格，不使用旧图风格"""
        # 主题关键词 → 视觉风格映射（更细粒度的映射）
        style_maps = {
            "代码": "minimalist code syntax lines on dark background, glowing green characters, terminal aesthetic, digital rain subtle",
            "Agent": "AI agent node network, autonomous decision flow, circular reasoning patterns, glowing blue nodes",
            "框架": "minimalist geometric framework structure, clean grid lines, modular building blocks, tech blueprint style",
            "LangChain": "Python code blocks on dark editor, chain-link patterns, function call graphs, developer workspace atmosphere",
            "AI": "neural network patterns, glowing data streams, tech circuit lines, deep tech blue",
            "算力": "GPU chip abstract, data center lights, computing power visualization",
            "一人": "solitary figure silhouette, vast space, one person infinite horizon",
            "组织": "organic network structure, interconnected nodes, team synergy flow",
            "认知": "brain neural connections, knowledge tree, mind map abstract",
            "创业": "startup rocket trajectory, growth curve, innovation spark",
            "商业": "market trend lines, business ecosystem, value chain network",
            "区块链": "blockchain chain structure, decentralized nodes, cryptographic patterns",
            "DAO": "decentralized organization network, governance nodes, token flow",
            "系统": "system architecture diagram, layered structure, modular design",
            "副业": "sunrise horizon, open laptop silhouette, freedom lifestyle, warm golden tones",
            "成长": "growth curve ascending, plant sprouting, upward trajectory, vibrant green tones",
            "道德经": "ink wash mountain, zen circle enso, bamboo silhouette, traditional eastern painting style, misty atmosphere",
            "无为": "zen garden, flowing water, empty space, wabi-sabi aesthetic, natural stone texture",
            "100行": "code editor dark theme, minimalist code lines, terminal aesthetic, glowing green monospace characters on very dark background, 100 lines motif subtle",
            "极简": "minimalist tech composition, clean lines, less is more, zen meets code, empty space with subtle coding elements",
            "原生化": "bare metal code aesthetic, raw terminal, no abstraction, direct system call vibe, pure code interface with dark background",
            "卸载": "clean slate digital, uninstall metaphor, minimal tech composition, clearing away complexity revealing simplicity",
        }
        # 默认：东方禅意 + 科技感
        visual_style = "dark zen background, ink wash mountain atmosphere, golden particles floating, oriental tech fusion"
        
        # 组合匹配：多个关键词叠加
        matched_styles = []
        search_terms = (keywords or []) + [topic]
        for term in search_terms:
            for key, style in style_maps.items():
                if key in term:
                    matched_styles.append(style)
        if matched_styles:
            visual_style = ", ".join(list(set(matched_styles))[:3])
        
        return (
            f"{visual_style}, "
            "minimalist composition with subtle golden accent particles, "
            "oriental aesthetic meets modern technology, high-end texture, cinematic lighting. "
            "NO text, NO letters. Pure background for article cover"
        )

    def _prompt_brand_header(self) -> str:
        return (
            "Dark elegant abstract background, golden geometric patterns, "
            "Chinese zen atmosphere, flowing light effects, "
            "minimalist and sophisticated. "
            "NO text, NO letters. Pure brand header background"
        )

    def _prompt_inline(self, style: str, topic: str = "",
                           keywords: list = None) -> str:
        """根据文章内容和配图样式生成背景创意
        按文章内容生成独特配图风格，不使用旧图风格"""
        # 主题关键词 → 视觉风格映射（更细粒度）
        style_maps = {
            "代码": "code editor dark theme, syntax highlighted lines, terminal window aesthetic, developer workspace",
            "Agent": "AI agent architecture diagram, autonomous decision nodes, circular data flow",
            "框架": "geometric framework grid, modular blocks, tech blueprint, clean structure lines",
            "LangChain": "function call graphs, chain connection nodes, Python code abstract",
            "AI": "neural network visualization, glowing data nodes, AI chip patterns",
            "算力": "GPU processor abstract, computing clouds, server farm lights",
            "一人": "solitary figure, vast open space, minimalist composition",
            "组织": "network organizational chart, connected nodes, team structure",
            "认知": "brain neural activity, knowledge visualization, mind map",
            "创业": "startup growth path, innovation sparks, entrepreneurial journey",
            "商业": "market data graphs, business ecosystem, value flow",
            "区块链": "chain of blocks, distributed network, cryptographic structure",
            "系统": "system architecture, modular flow diagram, layered design",
            "道德经": "zen garden pattern, flowing ink, bamboo silhouette, traditional scroll texture",
            "无为": "empty zen space, wabi-sabi textures, natural stone and water",
            "100行": "code editor minimalist, terminal window, green on black monospace text, 100 lines count subtle display, developer workspace zen",
            "极简": "minimalist tech zen, clean composition, bare essential code, empty elegant developer space",
        }
        base_style = "dark zen mood, subtle golden accents, minimalist composition, high-end texture"
        visual_keyword = ""
        if keywords:
            for kw in keywords:
                for key, style_str in style_maps.items():
                    if key in kw:
                        visual_keyword = style_str
                        break
        if not visual_keyword and topic:
            for key, style_str in style_maps.items():
                if key in topic:
                    visual_keyword = style_str
                    break
        
        style_prompts = {
            "diagram": f"Abstract flow diagram {visual_keyword or 'golden node connections'}, clean process arrows, professional diagram style",
            "info": f"Clean info visualization {visual_keyword or 'organized data cards'}, structured layout, data points",
            "concept": f"Central radial concept visualization {visual_keyword or 'core idea radiating'}, outward connections, knowledge graph style",
            "steps": f"Sequential process visualization {visual_keyword or 'progressive stages'}, step-by-step directional flow, clean stages",
            "quote": f"Minimalist quote background {visual_keyword or 'zen calm space'}, warm soft glow, elegant negative space, subtle atmosphere",
        }
        base = style_prompts.get(style, style_prompts["concept"])
        return f"{base}, {base_style}. NO text, NO letters. Pure background. "

    # ---- 文字叠加（复用 cover_generator 样式）----

    def _draw_cover_text(self, draw, w, h, title):
        """在Seedream背景上叠加觉知岛封面文字
        所有核心文字约束在中央 500×500 安全区（x:200~700）
        确保服务号列表、转发卡片 1:1 裁剪后文字完整可见"""
        SAFE_LEFT, SAFE_RIGHT = 200, 700
        SAFE_CX = (SAFE_LEFT + SAFE_RIGHT) // 2  # = 450

        # 品牌名（安全区内居中顶部）
        brand_text = f"\u25c6 {BRAND_NAME}"
        brand_font = _font(16, bold=True)
        bb_brand = brand_font.getbbox(brand_text)
        brand_w = bb_brand[2] - bb_brand[0]
        brand_x = SAFE_CX - brand_w // 2
        draw.text((brand_x, 20), brand_text,
                  fill=(*ACCENT, 240), font=brand_font)
        # 装饰线（品牌名下方居中）
        line_cx = SAFE_CX
        draw.line([(line_cx - 22, 44), (line_cx + 22, 44)],
                  fill=(*ACCENT, 140), width=1)
        draw.line([(line_cx - 16, 47), (line_cx + 16, 47)],
                  fill=(*ACCENT, 50), width=1)

        # 标题（安全区内居中，占主体）
        safe_w = SAFE_RIGHT - SAFE_LEFT - 40  # 460px 可用宽度
        f_title = _font(36, bold=True)
        lines, cur = [], ""
        for ch in title:
            test = cur + ch
            bb = f_title.getbbox(test)
            if bb and bb[2] > safe_w:
                lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            lines.append(cur)
        if not lines:
            lines = ["好文"]
        # 最多2行，第二行超长截断
        if len(lines) > 2:
            f_title = _font(28, bold=True)
            lines = lines[:2]
            if len(lines[1]) > 18:
                lines[1] = lines[1][:17] + "\u2026"

        # 计算标题总高度，垂直居中（在封面中间区域）
        lh = f_title.getbbox("测")[3] + 10
        total_h = len(lines) * lh + 8
        # 标题区域在封面高度方向居中偏上
        sy = (h - total_h) // 2 - 20

        for i, line in enumerate(lines):
            y_pos = sy + i * lh
            # 每行在安全区内居中
            bb_line = f_title.getbbox(line)
            line_w = bb_line[2] - bb_line[0]
            lx = SAFE_CX - line_w // 2
            # 文字阴影
            draw.text((lx + 1, y_pos + 1), line, fill=(0, 0, 0, 70), font=f_title)
            draw.text((lx, y_pos), line, fill=(*TEXT_WHITE, 250), font=f_title)

        # 道德经金句（安全区内，标题下方）
        motto_text = f"\u300c {MOTTO} \u300d"
        motto_font = _font(14)
        bb_motto = motto_font.getbbox(motto_text)
        motto_w = bb_motto[2] - bb_motto[0]
        motto_x = SAFE_CX - motto_w // 2
        my = sy + total_h + 30
        draw.text((motto_x, my), motto_text,
                  fill=(*ACCENT, 215), font=motto_font)

        # 分隔线（安全区内居中）
        sep_y = my + 28
        draw.line([(SAFE_CX - 22, sep_y), (SAFE_CX + 22, sep_y)],
                  fill=(*ACCENT, 140), width=1)
        draw.line([(SAFE_CX - 16, sep_y + 3), (SAFE_CX + 16, sep_y + 3)],
                  fill=(*ACCENT, 50), width=1)

        # 价值观（安全区内）
        values_font = _font(13)
        bb_vals = values_font.getbbox(VALUES)
        vals_w = bb_vals[2] - bb_vals[0]
        vals_x = SAFE_CX - vals_w // 2
        draw.text((vals_x, sep_y + 12), VALUES,
                  fill=(*ACCENT, 175), font=values_font)

        # 底部 tag（安全区内居中）
        ty = h - 26
        bb_tag = _font(13).getbbox(TAGLINE)
        tag_w = bb_tag[2] - bb_tag[0]
        draw.text((SAFE_CX - tag_w // 2, ty), TAGLINE, fill=(*TEXT_DIM, 190), font=_font(13))

    def _draw_brand_header_text(self, draw, w, h):
        """叠加品牌头图文字"""
        draw.text((30, 20), f"\u25c6 {BRAND_NAME}",
                  fill=(*ACCENT, 240), font=_font(22, bold=True))
        draw.text((30, 58), TAGLINE,
                  fill=(*TEXT_DIM, 180), font=_font(15))
        draw.text((30, 85), MOTTO,
                  fill=(*ACCENT, 160), font=_font(14))

        # 右下角价值观
        tw = _font(14).getbbox(VALUES)
        vw = tw[2] if tw else 200
        draw.text((w - 30 - vw, h - 30), VALUES,
                  fill=(*ACCENT, 120), font=_font(14))

    def _draw_inline_content(self, draw, w, h, content_text, style):
        """叠加配图文字——显示有实际信息价值的内容"""
        # 左上角品牌角标
        draw.text((16, 12), "◆", fill=(*ACCENT, 150), font=_font(14))

        # 根据样式绘制实际内容
        if style == "steps" and "→" in content_text:
            # 步骤图：显示步骤路线
            steps = content_text.split(" → ")
            fs = _font(18)
            for i, step in enumerate(steps[:4]):
                if i < 3:
                    draw.text((40, 50 + i * 55), f"  {step}", fill=(*TEXT_WHITE, 230), font=fs)
                    # 箭头
                    if i < len(steps) - 1:
                        draw.text((50, 50 + (i+1) * 55 - 28), "  ↓", fill=(*ACCENT, 150), font=_font(14))
                else:
                    draw.text((40, 50 + i * 55), f"  {step}", fill=(*TEXT_WHITE, 230), font=fs)
            draw.line([(30, h - 30), (w - 30, h - 30)], fill=(*ACCENT, 25), width=1)
        elif style == "concept":
            # 概念图：显示核心概念集群
            ft = _font(22)
            draw.text((w // 2 - 60, 30), "核心概念", fill=(*ACCENT, 180), font=_font(14))
            if " " in content_text:
                concepts = content_text.split(" ")
                for i, c in enumerate(concepts[:6]):
                    x = 40 + (i % 3) * 200
                    y = 70 + (i // 3) * 70
                    draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(*ACCENT, 200))
                    draw.text((x + 10, y - 8), c, fill=(*TEXT_WHITE, 220), font=_font(16))
            else:
                draw.text((40, 70), content_text[:40], fill=(*TEXT_WHITE, 230), font=_font(16))
            draw.line([(30, h - 30), (w - 30, h - 30)], fill=(*ACCENT, 25), width=1)
        elif style == "quote":
            # 金句图
            draw.text((30, 25), "“", fill=(*ACCENT, 120), font=_font(48))
            quote = content_text if len(content_text) <= 36 else content_text[:33] + "..."
            fq = _font(20)
            qlines, cur = [], ""
            for ch in quote:
                test = cur + ch
                bb = fq.getbbox(test)
                if bb and bb[2] > w - 100:
                    qlines.append(cur)
                    cur = ch
                else:
                    cur = test
            if cur:
                qlines.append(cur)
            for i, qline in enumerate(qlines):
                draw.text((40, 70 + i * 32), qline, fill=(*TEXT_WHITE, 230), font=fq)
            draw.text((w - 80, h - 35), "”", fill=(*ACCENT, 120), font=_font(48))
        else:
            # 默认为概念图风格
            draw.text((40, 50), content_text[:40], fill=(*TEXT_WHITE, 230), font=_font(18))
            draw.line([(20, h - 25), (w - 20, h - 25)], fill=(*ACCENT, 30), width=1)

    # ---- 对外接口（与 image_generator_enhanced 兼容）----

    def generate_cover(self, title: str, topic: str = "",
                       keywords: list = None) -> Path:
        """生成封面：Seedream 背景 + PIL 文字叠加"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_"
                           for c in title[:25])
        path = OUTPUT_DIR / f"cover_{safe_name}.png"

        if not self.enabled:
            raise RuntimeError("Seedream 未启用")

        # 根据文章主题生成背景提示词
        prompt = self._prompt_cover(topic=topic or title, keywords=keywords)
        bg = self.generate_background(prompt, 900, 383)
        draw = ImageDraw.Draw(bg, "RGBA")

        # 叠加文字
        self._draw_cover_text(draw, 900, 383, title)

        bg.save(path, "PNG", optimize=True)
        size_kb = path.stat().st_size / 1024
        print(f"\u2705 Seedream\u5c01\u9762\u56fe\u5df2\u751f\u6210: {path} ({size_kb:.0f} KB)")
        return path

    def generate_brand_header(self) -> Path:
        """生成品牌头图：Seedream 背景 + PIL 文字叠加"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_DIR / "brand_header.png"

        if not self.enabled:
            raise RuntimeError("Seedream 未启用")

        bg = self.generate_background(self._prompt_brand_header(), 900, 400)
        draw = ImageDraw.Draw(bg, "RGBA")
        self._draw_brand_header_text(draw, 900, 400)

        bg.save(path, "PNG", optimize=True)
        size_kb = path.stat().st_size / 1024
        print(f"\u2705 Seedream\u54c1\u724c\u5934\u56fe\u5df2\u751f\u6210: {path} ({size_kb:.0f} KB)")
        return path

    def generate_inline_image(self, title: str, style: str = "concept",
                              topic: str = "", width: int = 640,
                              height: int = 400) -> Path:
        """生成配图：Seedream 背景 + PIL 装饰文字"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_"
                           for c in title[:30])
        path = OUTPUT_DIR / f"inline_{safe_name}.png"

        if not self.enabled:
            raise RuntimeError("Seedream 未启用")

        # 根据文章主题和配图样式生成背景提示词
        prompt = self._prompt_inline(style, topic=topic or title, keywords=[topic] if topic else None)
        bg = self.generate_background(prompt, width, height)
        draw = ImageDraw.Draw(bg, "RGBA")
        self._draw_inline_content(draw, width, height, title, style)

        bg.save(path, "PNG", optimize=True)
        size_kb = path.stat().st_size / 1024
        print(f"\u2705 Seedream\u914d\u56fe\u5df2\u751f\u6210: {path} ({size_kb:.0f} KB)")
        return path


# ====== 快捷函数（与 image_generator_enhanced 接口一致） ======
def generate_cover_enhanced(title: str, topic: str = "",
                            keywords: list = None) -> Path:
    """尝试用 Seedream 生成封面，失败时回退到 PIL（image_generator_enhanced）"""
    try:
        from config import get_seedream_config
        cfg = get_seedream_config()
        if cfg.get("enabled") and cfg.get("access_key"):
            gen = SeedreamGenerator(cfg)
            return gen.generate_cover(title, topic, keywords)
    except Exception as e:
        print(f"  \u26a0\ufe0f Seedream 封面生成失败，回退到 PIL: {e}")

    from image_generator_enhanced import generate_cover_enhanced as fallback
    return fallback(title, topic, keywords)


def generate_inline_image(title: str, style: str = "concept",
                          topic: str = "", width: int = 640,
                          height: int = 400) -> Path:
    """尝试用 Seedream 生成配图，失败时回退到 PIL"""
    try:
        from config import get_seedream_config
        cfg = get_seedream_config()
        if cfg.get("enabled") and cfg.get("access_key"):
            gen = SeedreamGenerator(cfg)
            return gen.generate_inline_image(title, style, topic, width, height)
    except Exception as e:
        print(f"  \u26a0\ufe0f Seedream 配图生成失败，回退到 PIL: {e}")

    from image_generator_enhanced import generate_inline_image as fallback
    return fallback(title, style, topic, width, height)


# ====== 独立运行测试 ======
if __name__ == "__main__":
    print("=" * 50)
    print("Seedream 文生图模块测试")
    print("=" * 50)

    # 检查配置
    from config import get_seedream_config
    cfg = get_seedream_config()
    print(f"\nSeedream 配置状态:")
    print(f"  enabled: {cfg.get('enabled')}")
    print(f"  access_key: {'***' + cfg['access_key'][-4:] if cfg.get('access_key') else '空'}")
    print(f"  model: {cfg.get('model')}")

    if cfg.get("enabled") and cfg.get("access_key"):
        gen = SeedreamGenerator(cfg)
        print("\n测试文字叠加模块（不调用API）...")
        # 只测试 PIL 文字叠加，不调用 API
        bg = Image.new("RGB", (900, 383), (5, 8, 20))
        draw = ImageDraw.Draw(bg, "RGBA")
        gen._draw_cover_text(draw, 900, 383, "测试标题 123")
        test_path = OUTPUT_DIR / "test_text_overlay.png"
        bg.save(test_path)
        print(f"  \u2705 文字叠加测试通过: {test_path}")
        print("\n  API 调用需配置真实 access_key/secret_key")
        print("  用例: sg = SeedreamGenerator()")
        print("        cover = sg.generate_cover('你的标题', '你的主题')")
    else:
        print("\n  Seedream 未启用。如需启用:")
        print("  1. 在火山引擎控制台获取 AccessKey/SecretKey")
        print("  2. 在 config.json 中配置:")
        print('     "seedream": {')
        print('       "access_key": "AKxxx",')
        print('       "secret_key": "SKxxx",')
        print('       "enabled": true')
        print("     }")
        print("\n  3. 运行时自动使用 Seedream 生成封面/品牌图/配图")
        print("     若 Seedream 失败则自动回退到 PIL 生成")

# The following additions should be placed in the _prompt_cover style_maps dict.
# Adding new key mappings for better topic matching:
# "100行": "code editor dark theme, minimalist code lines, terminal aesthetic, glowing green monospace text on dark background, '100 lines' subtle motif"
# "极简": "minimalist tech composition, clean lines, less is more aesthetic, zen meets code, empty space with subtle coding elements"
# "卸载": "trash or uninstall icon abstract, digital clean slate, minimal tech uninstallation visual metaphor"
# "框架陷阱": "trap or maze geometric pattern, complex grid turning into simple path, minimal tech escape"
# "原生": "bare metal code, raw terminal, no abstraction layers, direct system call aesthetic, pure code interface"
