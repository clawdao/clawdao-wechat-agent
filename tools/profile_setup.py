#!/usr/bin/env python3
"""
品牌档案采集工具：首次使用时通过问答式对话完成 brand_profile.yml

> 用法：
>   交互模式：python3 tools/profile_setup.py
>   列出当前：python3 tools/profile_setup.py --show
>   重置默认：python3 tools/profile_setup.py --reset

> 工作方式：
> 1. 检查 brand_profile.yml 是否已存在
> 2. 不存在（或 --reset）就启动 8 个问题的访谈
> 3. 用户可以接受默认值（按 Enter）或输入自定义内容
> 4. 最后生成 brand_profile.yml 到项目根
"""
from __future__ import annotations
import sys
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from brand_profile import load_profile, PROFILE_PATH


# 8 个访谈问题
QUESTIONS = [
    {
        "key": "account.name",
        "label": "公众号名（中文）",
        "default": "亿检链",
        "hint": "出现在文章标题下方、署名、封面图水印",
    },
    {
        "key": "account.name_en",
        "label": "公众号英文名 / 缩写",
        "default": "LIMSCHAIN",
        "hint": "用于 LOGO、域名、英文场景",
    },
    {
        "key": "account.parent_brand",
        "label": "母品牌 / 所属公司",
        "default": "利姆斯科技旗下品牌",
        "hint": "可填：某某公司旗下 / 个人 IP / 无",
    },
    {
        "key": "account.slogan",
        "label": "一句话定位（slogan）",
        "default": "让企业运营可被验证",
        "hint": "整篇文章围绕它展开，建议 8-15 字",
    },
    {
        "key": "account.domain",
        "label": "内容领域（标签）",
        "default": "科技 · 商业 · 认知",
        "hint": "用 · 分隔多个领域",
    },
    {
        "key": "author.name",
        "label": "作者署名",
        "default": "顺道大叔",
        "hint": "每篇文章 author 字段都会显示这个",
    },
    {
        "key": "author.voice",
        "label": "文章风格描述",
        "default": "轻松专业，有深度但不晦涩",
        "hint": "AI 写文时会参考这个语气",
    },
    {
        "key": "wechat.default_style",
        "label": "默认发布风格",
        "default": "warm_gold",
        "hint": "列出已注册风格供选；不指定就默认 warm_gold",
    },
]


def ask(question: dict) -> str:
    """问一个问题，返回答案"""
    print(f"\n【{len(QUESTIONS)}/{len(QUESTIONS)}】{question['label']}")
    print(f"  💡 {question['hint']}")
    print(f"  默认：{question['default']}")
    answer = input("  你的回答（回车用默认）> ").strip()
    return answer or question["default"]


def collect_interactively() -> dict:
    """交互式收集答案"""
    print("=" * 60)
    print("🎨 欢迎使用 clawdao-wechat-agent！")
    print("=" * 60)
    print("我们需要 8 个简短问题来为你的公众号建立品牌档案。")
    print("每个问题直接回车就能用默认值。\n")

    profile = load_profile()  # 拿默认值

    for q in QUESTIONS:
        answer = ask(q)
        # 用点号路径写入嵌套 dict
        keys = q["key"].split(".")
        d = profile
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = answer

    # 作者签名（在 brand_assets 之外，加在 author 里）
    print(f"\n【附加】作者署名短句（结尾引用块出现）")
    print(f"  默认：{profile['profile']['author'].get('signature', '愿你的下一篇文章，写得比今天更轻松一点')}")
    sig = input("  你的回答（回车用默认）> ").strip()
    if sig:
        profile["profile"]["author"]["signature"] = sig

    return profile


def save_profile(profile: dict, path: Path = PROFILE_PATH) -> None:
    """把 profile dict 写成 yml 文件（手写格式以保持注释）"""
    import yaml
    p = profile["profile"]
    lines = [
        "# =============================================================================",
        "# 公众号品牌档案（Brand Profile）",
        "# =============================================================================",
        "# 这个文件由 tools/profile_setup.py 生成。",
        "# 重新生成会覆盖，建议先备份。",
        "# =============================================================================",
        "",
        "profile:",
        "  # ── 基本信息 ────────────────────────────────────────────────",
        "  account:",
        f"    name: \"{p['account']['name']}\"",
        f"    name_en: \"{p['account']['name_en']}\"",
        f"    parent_brand: \"{p['account']['parent_brand']}\"",
        f"    slogan: \"{p['account']['slogan']}\"",
        f"    domain: \"{p['account']['domain']}\"",
        f"    audience: \"{p['account']['audience']}\"",
        "",
        "  # ── 作者信息 ────────────────────────────────────────────────",
        "  author:",
        f"    name: \"{p['author']['name']}\"",
        f"    signature: \"{p['author']['signature']}\"",
        f"    voice: \"{p['author']['voice']}\"",
        "",
        "  # ── 品牌资产 ────────────────────────────────────────────────",
        "  brand_assets:",
        f"    cover_image: \"{p['brand_assets']['cover_image']}\"",
        f"    brand_header: \"{p['brand_assets']['brand_header']}\"",
        f"    square_share: \"{p['brand_assets']['square_share']}\"",
        f"    official_header: \"{p['brand_assets']['official_header']}\"",
        "",
        "  # ── 品牌色 ────────────────────────────────────────────────",
        "  colors:",
        f"    primary: \"{p['colors']['primary']}\"",
        f"    primary_alt: \"{p['colors']['primary_alt']}\"",
        f"    accent: \"{p['colors']['accent']}\"",
        f"    text: \"{p['colors']['text']}\"",
        f"    text_muted: \"{p['colors']['text_muted']}\"",
        "",
        "  # ── 微信配置 ───────────────────────────────────────────────",
        "  wechat:",
        f"    default_style: \"{p['wechat']['default_style']}\"",
        f"    default_author: \"{p['author']['name']}\"",
        f"    cover_width: {p['wechat']['cover_width']}",
        f"    cover_height: {p['wechat']['cover_height']}",
        f"    brand_header_width: {p['wechat']['brand_header_width']}",
        f"    brand_header_height: {p['wechat']['brand_header_height']}",
        "",
        "  # ── GEO（生成式引擎优化）默认内容 ─────────────────────────",
        "  geo:",
        f"    publisher_name: \"{p['geo']['publisher_name']}\"",
        f"    publisher_description: \"{p['geo']['publisher_description']}\"",
        f"    publisher_type: \"{p['geo']['publisher_type']}\"",
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def cmd_show():
    """展示当前 profile"""
    p = load_profile()["profile"]
    print("\n=== 当前 brand_profile.yml ===")
    print(f"账号     : {p['account']['name']} ({p['account']['name_en']})")
    print(f"母品牌   : {p['account']['parent_brand']}")
    print(f"Slogan   : {p['account']['slogan']}")
    print(f"内容领域 : {p['account']['domain']}")
    print(f"作者     : {p['author']['name']}")
    print(f"风格     : {p['wechat']['default_style']}")
    print(f"品牌头图 : {p['brand_assets']['brand_header']}")
    print(f"作者签名 : {p['author'].get('signature', '-')}")
    print()


def cmd_reset():
    """删除 profile，重新采集"""
    if PROFILE_PATH.exists():
        backup = PROFILE_PATH.with_suffix(".yml.bak")
        shutil.copy(PROFILE_PATH, backup)
        print(f"💾 已备份到 {backup}")
        PROFILE_PATH.unlink()
        print("🗑️  已删除 brand_profile.yml")
    profile = collect_interactively()
    save_profile(profile)
    print(f"\n✅ 已生成 {PROFILE_PATH}")
    print("💡 提示：可以编辑 brand_profile.yml 微调任意字段")


def cmd_init():
    """首次初始化（如果不存在）"""
    if PROFILE_PATH.exists():
        print(f"⚠️  brand_profile.yml 已存在")
        print("   用 --reset 重新生成 / --show 查看当前内容")
        return
    profile = collect_interactively()
    save_profile(profile)
    print(f"\n✅ 已生成 {PROFILE_PATH}")
    print("💡 提示：可以编辑 brand_profile.yml 微调任意字段")


# ── CLI ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="品牌档案采集工具")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--show", action="store_true", help="展示当前 profile")
    g.add_argument("--reset", action="store_true", help="重置并重新采集")
    args = p.parse_args()

    if args.show:
        cmd_show()
    elif args.reset:
        cmd_reset()
    else:
        cmd_init()
