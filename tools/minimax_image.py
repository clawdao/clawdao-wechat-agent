"""MiniMax 图生图客户端 — 适配公众号封面与配图"""
import base64
import json
import os
import time
from pathlib import Path

import requests

from config import get_minimax_image_config


class MinimaxImage:
    """MiniMax image-01 文生图客户端。

    端点：POST {base_url}{endpoint}
    请求体（参考 minimax 文档）：
      {
        "model": "image-01",
        "prompt": "...",
        "width": 1024,
        "height": 1024,
        "n": 1
      }
    响应：{"images": [{"image_url": "https://..."} 或 "base64": "..."}]}
    """

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or get_minimax_image_config()
        self.base_url = self.cfg["base_url"].rstrip("/")
        self.endpoint = self.cfg.get("endpoint", "/v1/image_generation")
        self.model = self.cfg.get("model", "image-01")
        self.api_key = self.cfg.get("api_key", "")
        self.default_size = self.cfg.get("size", "1024x1024")
        self.timeout = 120

    @property
    def enabled(self) -> bool:
        return bool(self.cfg.get("enabled")) and bool(self.api_key) and not self.api_key.startswith("your-")

    def _url(self) -> str:
        return f"{self.base_url}{self.endpoint}"

    def generate(self, prompt: str, out_path: str | Path,
                 width: int | None = None, height: int | None = None,
                 n: int = 1) -> str | None:
        """生成图片并保存到 out_path（绝对或相对 cwd 的路径）。返回最终路径或 None（失败）"""
        if not self.enabled:
            print(f"  [minimax_image] 未启用或缺 key，跳过")
            return None
        if not prompt:
            print("  [minimax_image] prompt 为空")
            return None
        if width is None or height is None:
            try:
                w, h = map(int, self.default_size.lower().split("x"))
                width = width or w
                height = height or h
            except Exception:
                width, height = 1024, 1024
        body = {
            "model": self.model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "n": n,
        }
        try:
            r = requests.post(
                self._url(),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  [minimax_image] 调用失败: {e}")
            return None
        # 解析响应：minimax image-01 实际字段为 data.image_urls[0]（列表）
        images = (data.get("data") or {}).get("image_urls") or data.get("image_urls")
        url_or_b64 = None
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict):
                url_or_b64 = (first.get("url") or first.get("image_url")
                              or first.get("b64_json") or first.get("base64"))
            elif isinstance(first, str):
                url_or_b64 = first
        elif isinstance(images, str):
            url_or_b64 = images
        if not url_or_b64:
            url_or_b64 = (data.get("data") or {}).get("image_url") or data.get("url") or data.get("image")
        if not url_or_b64:
            print(f"  [minimax_image] 响应未发现图片字段: keys={list(data.keys())}")
            return None
        # 保存（支持 URL 或 base64）
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            if url_or_b64.startswith("data:") or len(url_or_b64) > 1024 and not url_or_b64.startswith("http"):
                # 视为 base64
                b64 = url_or_b64.split(",", 1)[-1]
                out.write_bytes(base64.b64decode(b64))
            elif url_or_b64.startswith("http"):
                img = requests.get(url_or_b64, timeout=60)
                img.raise_for_status()
                out.write_bytes(img.content)
            else:
                out.write_bytes(base64.b64decode(url_or_b64))
            return str(out)
        except Exception as e:
            print(f"  [minimax_image] 保存失败: {e}")
            return None


def is_available() -> bool:
    return MinimaxImage().enabled
