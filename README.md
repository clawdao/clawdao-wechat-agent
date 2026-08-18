# clawdao-wechat-factory · 公众号工厂

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

> 🔐 安全提示：`config.json` 含真实密钥，**不要**提交到 Git。模板见 `config.example.json`。

## 📁 目录结构

```
.
├── main.py                    # 主入口：一键 文章+封面+配图+发布
├── article_generator.py       # AI 文章生成（GEO 优化）
├── cover_generator.py         # 封面图生成（基础版 / Deluxe / 定制版）
├── image_generator_enhanced.py# 增强图像生成
├── wechat_publisher.py        # 微信草稿箱发布
├── config.py / config.json    # 配置（config.json 已忽略入库）
├── config.example.json        # 脱敏配置模板
└── docs/                      # 选题规划文档
```

## ⚖️ 许可

MIT
