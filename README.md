# clawdao-wechat-agent · 公众号自动发布智能体

> 公众号内容自动化生产流水线：**多风格模板 → AI 撰写文章 → 精美封面/配图 → 一键发布微信草稿箱**。

![license](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.10+-blue)

---

## ✨ 功能特性

| 能力 | 说明 |
| --- | --- |
| 🎨 **多风格模板系统** | YAML 风格的样式注册表（`styles/*.yml`），可切换、可学习、可热插拔 |
| 📚 **从链接学习风格** | 给定微信文章 URL，自动提取主色/装饰/排版特征，生成新的 `.yml` 风格文件 |
| ✍️ **AI 文章生成** | 基于 MiniMax-M3，内置 GEO 提示词（实体词密度、问答模式、数据锚点） |
| 🖼️ **封面 + 内联配图** | 封面自动上传作 `thumb_media_id`，文中 `![alt](path)` 自动上传到微信 CDN |
| 📤 **一键发布草稿箱** | 风格化渲染 → 处理配图 → 品牌头图置顶 → 推送到 `/cgi-bin/draft/add` |
| 🏷️ **智能标签 + GEO** | 自动生成关键词 + 注入 JSON-LD 结构化数据，利于 AI 搜索引用 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pyyaml requests openai Pillow
```

### 2. 配置密钥

```bash
cp config.example.json config.json
# 编辑 config.json：填入 MiniMax / 微信 AppSecret / Seedream 密钥
```

### 3. 三种发布姿势

#### 姿势 A：用内置风格发布
```bash
# 列已注册风格
python3 core/publish_v2.py --list-styles

# 用 warm_gold 风格发布
python3 core/publish_v2.py \
  --style warm_gold \
  --title "我的文章标题" \
  --in content.md \
  --cover outputs/cover.png \
  --brand-header outputs/brand_header.png \
  --delete-old <旧media_id>   # 可选：删除旧草稿
```

#### 姿势 B：先学风格，再用 style 文件发布
```bash
# 第 1 步：从一篇参考文章学习风格
python3 tools/style_learner.py \
  --url "https://mp.weixin.qq.com/s/..." \
  --name my_style \
  --description "我的风格"

# 第 2 步：用学到的风格发布
python3 core/publish_v2.py \
  --style my_style \
  --title "..." \
  --in content.md
```

#### 姿势 C：先渲染，再发布（调试用）
```bash
# 第 1 步：单独渲染为 HTML（可预览）
python3 core/style_renderer.py \
  --style warm_gold \
  --in content.md \
  --out article.html

# 第 2 步：手工检查 article.html 后再发布
python3 core/publish_v2.py \
  --style warm_gold \
  --title "..." \
  --in content.md
```

---

## 📁 项目结构

```
clawdao-wechat-agent/
├── README.md                          ← 你正在读的文件
├── AGENTS.md                          ← 亿检链排版规范（紫蓝渐变）
├── config.json                        ← 全局配置（API/微信/封面/输出）
│
├── 🎨 styles/                          ← 🆕 风格注册表
│   ├── tech_blue.yml                   亿检链默认（紫蓝渐变）
│   ├── warm_gold.yml                   温暖金色（手工调优）
│   └── learned/                        从 URL 自动学习的风格
│       └── warm_gold_v2.yml
│
├── 🔧 core/
│   ├── style_renderer.py               ← 🆕 markdown + 风格 → HTML（唯一入口）
│   ├── publish_v2.py                   ← 🆕 风格化发布器（支持内联图片 + 品牌头图）
│   ├── publisher.py                    ← 旧版发布器（保留兼容）
│   └── article.py                      ← AI 写文
│
├── 🛠️ tools/
│   ├── style_learner.py                ← 🆕 从 URL 学习风格
│   ├── style_learner_image.py          ← ⏳ 从图片学习风格（TODO）
│   ├── article_styles.py               ← 旧版样式模块（保留兼容）
│   ├── minimax_image.py                ← 图像生成
│   ├── seedream.py                     ← Seedream 图像生成
│   └── yijianlian_*.py                 ← 品牌封面/插图
│
├── 🖼️ covers/                          ← 封面图工具（多个版本，建议清理）
├── 📤 publish/                          ← 旧版发布脚本（多个版本，建议清理）
│
├── 📝 output/                           ← 渲染后的 HTML、预览图、发布结果
└── 🖼️ outputs/                          ← 封面图、内联插图（最终素材）
```

---

## 🎨 风格系统详解

### YAML 风格文件结构

```yaml
meta:
  name: warm_gold
  display_name: "温暖金色"
  source_url: "https://mp.weixin.qq.com/s/..."
  learned_at: "2026-09-30"
  tags: ["东方", "禅意", "金色"]

palette:
  primary: "#c8a84e"        # 主金色
  primary_dark: "#a07d30"
  primary_soft: "#f5f0e8"   # 浅金底
  text_primary: "#1a1a2e"

components:
  h1:                       # 一级标题组件
    container: 'margin: 0 0 20px 0; text-align: center;'
    title:     'font-size: 18px; ...'
    deco:      'width: 36px; height: 3px; ...'
  h2:                       # 二级标题
    container: 'margin: 28px 0 14px 0;'
    flex:      'display: flex; align-items: center;'
    bar:       'width: 4px; height: 20px; background: #c8a84e; ...'
    title:     'font-size: 17px; ...'
  p:
    base:      'margin: 8px 0; font-size: 15px; ...'
  strong:
    base:      'font-weight: bold; color: #c8a84e;'
  blockquote:
    container: 'background: #f5f0e8; border-left: 4px solid #c8a84e; ...'
    text:      'margin: 0; font-size: 14px; ...'
  hr:
    container: 'margin: 28px 0; text-align: center; color: #c8a84e; ...'
    content:   '✦ ✦ ✦'

rendering:
  limits:
    max_blockquotes: 2      # 引用块不超过 2 处
    max_strong_per_p: 2
  decoration:
    separator: "✦ ✦ ✦"
```

### 添加自定义风格

1. **手工编写**：复制 `styles/warm_gold.yml`，改色号和组件 CSS
2. **从 URL 学习**：`python3 tools/style_learner.py --url <url> --name my_style`
3. **从图片学习**（TODO）：`python3 tools/style_learner_image.py --image <img> --name my_style`

风格自动注册到 `styles/` 或 `styles/learned/`，下次发布直接 `--style my_style`。

---

## 🔄 完整工作流（从选题到发布）

```bash
# Step 1: 准备选题和大纲
# （人工或从 Obsidian 知识库拉取）

# Step 2: 写 Markdown 文章（含内联图片引用）
cat > article.md << 'EOF'
# 我的文章标题

> 写给每一个想好好说话的人

![配图说明](./outputs/inline_1.png)

## 一、小标题

正文段落。**关键概念**。

## 二、小标题

更多正文。
EOF

# Step 3: 选风格 + 渲染预览（可选）
python3 core/style_renderer.py \
  --style warm_gold \
  --in article.md \
  --out article_preview.html
open article_preview.html  # 在浏览器看手机端预览

# Step 4: 一键发布到微信草稿箱
python3 core/publish_v2.py \
  --style warm_gold \
  --title "我的文章标题" \
  --in article.md \
  --cover outputs/cover.png \
  --brand-header outputs/brand_header.png
# 输出：media_id（请到公众号后台草稿箱查看）

# Step 5: 重复发布时，先删除旧的
python3 core/publish_v2.py \
  --style warm_gold \
  --title "我的文章标题" \
  --in article.md \
  --delete-old <旧media_id>
```

---

## 🐞 常见问题

### Q1：草稿箱摘要显示 HTML 标签（`<section style="...">`）

**原因**：摘要生成时用了 HTML 内容，HTML 头被当成摘要文本。
**解决**：v2.0+ 已修复——摘要从 markdown 提取纯文本。

### Q2：内联图片显示占位符（`[图片: ...]`）

**原因**：图片未上传到微信 CDN。
**解决**：v2.0+ 已修复——自动扫描 `<img src="./local.png">`，上传到 `/cgi-bin/media/uploadimg`，替换为微信 URL。

### Q3：正文里没有头图

**原因**：默认按 AGENTS.md 永久约束"正文不放封面图"。
**解决**：用 `--brand-header <img>` 在正文顶部插入品牌头图（区别于推送封面图 `thumb_media_id`）。

### Q4：风格变了

**原因**：旧版 `core/publisher._markdown_to_html` 写死金色样式，绕过了 AGENTS.md 规范。
**解决**：所有发布走 `core/publish_v2.py`，它直接接收 `StyleRenderer` 渲染的 HTML，不再二次转换。

---

## 🧪 测试与验证

```bash
# 1. 验证风格渲染
python3 core/style_renderer.py --list-styles
python3 -c "
from core.style_renderer import StyleRenderer
r = StyleRenderer('warm_gold')
print(r.render('# 标题\n\n正文 **加粗**'))
"

# 2. 验证风格学习
python3 tools/style_learner.py \
  --url "https://mp.weixin.qq.com/s/YBnmY042Y39FobbhWI_92A" \
  --name test_warm_gold \
  --description "测试温暖金色"
ls styles/learned/test_warm_gold.yml

# 3. 验证发布（不需要真的发布）
python3 -c "
from core.publish_v2 import list_styles
print(list_styles())
"
```

---

## 📚 历史版本

- **v1**（旧）：`core/publisher.save_as_draft` —— 直接 markdown，内部 `_markdown_to_html` 写死金色样式
- **v2**（当前）：`core/publish_v2.publish_with_style` —— 接受风格名，调用 `StyleRenderer`，处理内联图片 + 品牌头图
- 旧版 `core/publisher.py` 保留作为兼容入口

---

## 📝 开发规范

1. **风格 ≠ 流程**：所有样式集中在 `styles/*.yml`，不在代码里硬编码
2. **单一入口**：markdown → HTML 走 `core/style_renderer.py`；HTML → 微信走 `core/publish_v2.py`
3. **可学习**：从 URL/图片提取风格，避免手工调样式
4. **不破坏旧规则**：AGENTS.md 永久约束（正文不放封面图、500×500 安全区等）仍生效

