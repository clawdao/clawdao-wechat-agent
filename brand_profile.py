"""
品牌档案加载器：从 brand_profile.yml 读取公众号个性化信息

> 设计目的：
> 把所有"公众号专属信息"集中到一个 yml 文件，让一个项目服务多个公众号用户。
> 第一次使用时，运行 `python3 tools/profile_setup.py` 完成采集。

> 兼容性：
> 如果 yml 不存在，会返回硬编码的默认值（向后兼容，确保旧代码不崩）。
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import yaml

PROJECT_DIR = Path(__file__).parent
PROFILE_PATH = PROJECT_DIR / "brand_profile.yml"


def _default_profile() -> dict:
    """默认 profile（兜底）——兼容旧的硬编码行为"""
    return {
        "profile": {
            "account": {
                "name": "亿检链",
                "name_en": "LIMSCHAIN",
                "parent_brand": "利姆斯科技旗下品牌",
                "slogan": "让企业运营可被验证",
                "domain": "科技 · 商业 · 认知",
                "audience": "科技从业者、创业者、认知升级人群、企业运营者",
            },
            "author": {
                "name": "顺道大叔",
                "signature": "愿你的下一篇文章，写得比今天更轻松一点",
                "voice": "轻松专业，有深度但不晦涩",
            },
            "brand_assets": {
                "cover_image": "images/亿检链_文章封面_900x500.png",
                "brand_header": "images/亿检链_头图横幅_900x383.png",
                "square_share": "images/亿检链_分享小图_500x500.png",
                "official_header": "images/亿检链_头图横幅_官方_1600x640.png",
            },
            "colors": {
                "primary": "#0a2e7a",
                "primary_alt": "#1e6dff",
                "accent": "#f24c3a",
                "text": "#333333",
                "text_muted": "#888888",
            },
            "wechat": {
                "default_style": "warm_gold",
                "default_author": "顺道大叔",
                "cover_width": 900,
                "cover_height": 500,
                "brand_header_width": 900,
                "brand_header_height": 383,
            },
            "geo": {
                "publisher_name": "亿检链",
                "publisher_description": "东方智慧 + 现代科技，AI时代的认知升级平台",
                "publisher_type": "Organization",
            },
        }
    }


def load_profile(path: Path | str = PROFILE_PATH) -> dict:
    """读取 brand_profile.yml，不存在则返回默认 dict"""
    p = Path(path)
    if not p.exists():
        return _default_profile()
    try:
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "profile" not in data:
            return _default_profile()
        # 缺失字段用默认值补全
        default = _default_profile()["profile"]
        for section, defaults in default.items():
            if section not in data["profile"]:
                data["profile"][section] = defaults
            else:
                for key, val in defaults.items():
                    data["profile"][section].setdefault(key, val)
        return data
    except Exception as e:
        print(f"⚠️  读取 brand_profile.yml 失败：{e}，使用默认")
        return _default_profile()


# 便捷访问
_profile_cache: dict | None = None


def get_profile() -> dict:
    """获取 profile dict（带缓存）"""
    global _profile_cache
    if _profile_cache is None:
        _profile_cache = load_profile()
    return _profile_cache


def account() -> dict:
    """公众号账号信息"""
    return get_profile()["profile"]["account"]


def author() -> dict:
    """作者信息"""
    return get_profile()["profile"]["author"]


def brand_assets() -> dict:
    """品牌资产路径"""
    return get_profile()["profile"]["brand_assets"]


def colors() -> dict:
    """品牌色"""
    return get_profile()["profile"]["colors"]


def wechat() -> dict:
    """微信相关配置"""
    return get_profile()["profile"]["wechat"]


def geo() -> dict:
    """GEO 配置"""
    return get_profile()["profile"]["geo"]


def reset_cache() -> None:
    """重置缓存（测试或修改 profile 后调用）"""
    global _profile_cache
    _profile_cache = None


# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = get_profile()["profile"]
    print(f"账号: {p['account']['name']} ({p['account']['name_en']})")
    print(f"作者: {p['author']['name']}")
    print(f"风格: {p['wechat']['default_style']}")
    print(f"品牌头图: {p['brand_assets']['brand_header']}")
