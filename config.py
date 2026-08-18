"""配置管理模块"""
import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_api_config():
    cfg = load_config()
    return cfg["api"]


def get_wechat_config():
    cfg = load_config()
    return cfg["wechat"]


def get_cover_config():
    cfg = load_config()
    return cfg["cover"]


def get_output_config():
    cfg = load_config()
    return cfg["output"]


def get_output_dir():
    cfg = get_output_config()
    out_dir = Path(__file__).parent / cfg["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def get_seedream_config():
    cfg = load_config()
    return cfg.get("seedream", {
        "access_key": "",
        "secret_key": "",
        "endpoint": "https://visual.volcengineapi.com",
        "model": "high_aes_general_v30l_zt2i",
        "enabled": False,
    })
