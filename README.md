# clawdao-wechat-agent · 公众号自动发布智能体

> 公众号内容自动化生产流水线：**AI 撰写文章（GEO 优化）→ 精美封面/配图 → 一键发布微信草稿箱**。

![license](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.10+-blue)

## ✨ 功能特性

| 能力 | 说明 |
| --- | --- |
| ✍️ **AI 文章生成** | 基于 DeepSeek 大模型，内置 **GEO（生成式引擎优化）** 提示词：实体词密度、问答模式、数据锚点、语义层级、互链概念 |
| 🖼️ **封面图生成** | 精美封面（900×383）+ 文章内部配图，支持多种风格模板（简约 / Deluxe / 定制） |
| 📤 **微信发布** | 一键写入微信草稿箱（文章 + 封面 + 标签），支持批量与智能发布 |
| 🏷️ **智能标签** | 根据选题自动生成关键词标签（副业/AI/认知/道德经/区块链/IP 等主题映射） |

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置密钥（复制模板并填写）
cp config.example.json config.json
#   编辑 config.json：填入 DeepSeek / 微信 AppSecret / Seedream 密钥

# 3. 一键生成并发布
python3 main.py "AI时代如何提升个人效率" --style 轻松专业
#   可选参数：--no-publish（仅生成不发布） / --no-cover（不生成封面）
```

## ⚙️ 配置说明

密钥统一放在 `config.json`（**已被 .gitignore 忽略，严禁提交**）：

| 配置段 | 字段 | 说明 |
| --- | --- | --- |
| `api` | `base_url` / `api_key` / `chat_model` / `image_model` | DeepSeek / 图像模型 |
| `wechat` | `appid` / `appsecret` | 微信公众平台凭证（用于写入草稿箱） |
| `seedream` | `access_key` / `secret_key` / `model` | 火山方舟 Seedream 图像生成 |
| `cover` | `width` / `height` / 配色 | 封面尺寸与主题色 |
| `output` | `dir` / 前缀 | 产物输出目录 |

## 📁 目录结构

```
.
├── main.py                  🚀 CLI 入口（一键主入口）
├── config.py                ⚙️ 配置加载
│
├── core/                    📚 核心流程
│   ├── article.py           ✍️ AI 文案生成
│   └── publisher.py         📤 微信草稿箱发布
│
├── covers/                  🖼️ 封面图生成
│   ├── base.py              基础版
│   ├── deluxe.py            Deluxe 版（径向+线性渐变）
│   ├── lite.py              减少依赖版
│   ├── themed.py            主题版
│   ├── enhanced.py          增强版（main 默认）
│   ├── banner.py            标题横幅
│   ├── helper.py            辅助函数
│   └── regen.py             图片重新生成
│
├── publish/                 📤 发布工具
│   ├── smart.py             主用（智能同步品牌头图）
│   ├── single.py            单篇
│   ├── batch.py             批量
│   ├── final.py             最终版
│   ├── v2.py / v3.py        旧版本（保留）
│   ├── both.py              同时发布两篇
│   └── republish.py         重发布 OPD
│
├── tools/                   🔧 工具/集成
│   ├── seedream.py          火山方舟 Seedream 图像
│   ├── opd.py               OPD 业务文章
│   ├── fix.py               修复工具
│   ├── patch_doc.py         文档补丁
│   └── volcengine_sign.py   签名测试
│
├── tests/                   🧪 单元测试（unittest）
│   ├── test_config.py
│   ├── test_core_article.py
│   ├── test_core_publisher.py
│   └── test_covers.py
│
└── docs/                    📖 文档
    └── REFACTORING-PLAN.md  重构计划
```


## ⚖️ 许可

Apache-2.0
