"""配置管理模块"""
import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
CLAWDAO_AUTH_PATH = Path.home() / ".clawdao" / "auth.json"


def _load_clawdao_key(provider: str) -> str | None:
    """从 ~/.clawdao/auth.json 加载指定 provider 的 key（如 minimax-cn）"""
    if not CLAWDAO_AUTH_PATH.exists():
        return None
    try:
        with open(CLAWDAO_AUTH_PATH) as f:
            auth = json.load(f)
        entry = auth.get(provider, {})
        if isinstance(entry, dict):
            return entry.get("key")
    except Exception:
        return None
    return None


def _resolve_api_key(cfg_section: dict, provider: str = "minimax-cn") -> str:
    """解析 api_key 字段：
    - 如果是 'auto-from-auth-json'，从 ~/.clawdao/auth.json 取
    - 否则直接使用字面值
    """
    key = cfg_section.get("api_key", "")
    if key == "auto-from-auth-json" or not key:
        loaded = _load_clawdao_key(provider)
        if loaded:
            return loaded
    return key


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_config():
    """加载 config 并自动注入从 auth.json 解析出的 key"""
    cfg = load_config()
    # 文本 API
    if "api" in cfg:
        cfg["api"]["api_key"] = _resolve_api_key(cfg["api"], provider="minimax-cn")
    # 图像 API
    if "minimax_image" in cfg:
        cfg["minimax_image"]["api_key"] = _resolve_api_key(cfg["minimax_image"], provider="minimax-cn")
    return cfg


def get_api_config():
    return _resolve_config()["api"]


def get_wechat_config():
    return load_config()["wechat"]


def get_cover_config():
    return load_config()["cover"]


def get_output_config():
    return load_config()["output"]


def get_output_dir():
    cfg = get_output_config()
    out_dir = Path(__file__).parent / cfg["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def get_minimax_image_config():
    """MiniMax 图像生成配置（默认图像生成）"""
    cfg = _resolve_config()
    return cfg.get("minimax_image", {
        "enabled": True,
        "base_url": "https://api.minimaxi.com",
        "api_key": "",
        "model": "image-01",
        "endpoint": "/v1/image_generation",
        "size": "1024x1024",
        "default_params": {"width": 1024, "height": 1024, "n": 1},
    })


def get_seedream_config():
    """Seedream（火山方舟）配置，作为 minimax_image 的回退"""
    cfg = load_config()
    return cfg.get("seedream", {
        "access_key": "",
        "secret_key": "",
        "endpoint": "https://visual.volcengineapi.com",
        "model": "high_aes_general_v30l_zt2i",
        "enabled": False,
        "use_as_fallback": True,
    })


def get_image_provider():
    """按优先级选择当前图像 Provider（minimax_image 优先，seedream 回退）"""
    mm = get_minimax_image_config()
    if mm.get("enabled") and mm.get("api_key") and not mm["api_key"].startswith("your-"):
        return "minimax_image", mm
    sd = get_seedream_config()
    if sd.get("enabled", True) and sd.get("access_key") and not sd["access_key"].startswith("your-"):
        return "seedream", sd
    return None, None
