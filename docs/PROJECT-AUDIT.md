# 项目扫描报告

> 扫描时间：2026-09-30
> 范围：`/Users/imfly/projects/Agents/clawdao-wechat-agent`
> 目的：发布链路反复飘逸的根本原因诊断

---

## 一、问题清单（按严重程度）

### 🔴 P0 — 阻塞性问题（直接导致"飘逸"）

| # | 问题 | 影响 | 证据 |
|---|------|------|------|
| 1 | **样式定义散落 3 处，互相不一致** | 不同入口渲染出不同风格 | AGENTS.md（紫蓝渐变 #667eea→#764ba2）<br>core/publisher.py（金色 #c8a84e）<br>tools/article_styles.py（科技蓝 #0a2e7a） |
| 2 | **`core/publisher._markdown_to_html` 写死金色样式** | 即便 HTML 正确传入，仍被二次转换覆盖 | `core/publisher.py:189` `_markdown_to_html` 内 `C_ACCENT = "#c8a84e"` |
| 3 | **没有"风格"概念** | 只能选"亿检链科技蓝"或"手工 HTML"，无法学新风格 | `tools/article_styles.py` 只暴露 `build_article_html` 单函数 |
| 4 | **没有"风格学习"机制** | 无法从图片/链接反向提取风格 | 无任何 scraper、style extractor |
| 5 | **`save_as_draft` 不支持直接传 HTML** | 手动渲染的 HTML 会被 `_markdown_to_html` 覆盖 | `core/publisher.py:102` 强制走 `_markdown_to_html` |

### 🟠 P1 — 重复/可维护性

| # | 问题 | 证据 |
|---|------|------|
| 6 | **publish/ 目录有 8 个版本**（single/v2/v3/final/smart/republish/both/batch） | `publish/` |
| 7 | **covers/ 目录有 7 个版本**（base/deluxe/enhanced/helper/lite/regen/themed/banner） | `covers/` |
| 8 | **`tools/article_styles.py` 的 H1/H2/Quote CSS 与 AGENTS.md 数值一致**，但**逻辑有 bug**：`p()` 把 `>...**...**` 当普通段落处理，破坏引用块 | `tools/article_styles.py:127-141` |
| 10 | **`branch: cleanup`** 没有任务追踪 | 派单文件、发布、回退无法追溯 |

### 🟡 P2 — 用户期望但缺失 |
| # | 问题 | 期望 |
|---|------|------|
| 11 | **风格选择 UI** | 用户希望发布时选"科技蓝/温暖金色/..." |
| 12 | **从 URL 学习风格** | 给定微信文章链接，能解析出风格模板 |
| 13 | **从图片学习风格** | 给定封面/截图，能提取色板+排版特征 |
| 14 | **风格库管理** | 已学风格可命名、可复用、可对比 |

---

## 二、架构现状

```
公众号智能体/
├── AGENTS.md               # 排版规范（紫蓝渐变 #667eea→#764ba2）
├── config.json             # 全局配置
├── main.py                 # 主流程入口（依赖多，外部脚本易跑失败）
├── core/
│   ├── article.py          # AI 写文
│   └── publisher.py        # 发布（_markdown_to_html 写死金色样式）
├── covers/                 # 封面图（7 个版本互相覆盖）
├── tools/article_styles.py # 通用模板（紫蓝渐变）
└── publish/                # 发布脚本（8 个版本）
```

### 调用链
```
main.py → core/article.generate_article (openai)
       → covers/enhanced.generate_cover (PIL)
       → core/publisher.save_as_draft
         → _markdown_to_html (写死 #c8a84e 金色) ← 罪魁祸首
         → _get_access_token
         → /cgi-bin/draft/add
```

**为什么"飘逸"**：每次发布走不同路径：
- v1：`tools/article_styles.build_article_html` → 自己 markdown 预处理 → 调 `save_as_draft` → 被 `_markdown_to_html` 覆盖
- v2：手工写 HTML → `output/publish_v2.py` 直接调 `_get_access_token` → 绕过 `_markdown_to_html`

两条路径风格不一致，且没有任何"风格"配置入口。

---

## 三、目标架构

### 核心思想：**Style-First Design**

```
                     ┌──────────────┐
                     │   AGENTS.md  │  ← 真理之源
                     └──────┬───────┘
                            │ 单向引用
                            ▼
        ┌──────────────────────────────────┐
        │  styles/  ←─ 风格注册表（YAML）   │
        │  ├── tech_blue.yml   (亿检链默认)  │
        │  ├── warm_gold.yml   (温暖金色)   │
        │  └── learned/*.yml   (从学习生成) │
        └──────────────┬───────────────────┘
                       │ load_style(name)
                       ▼
        ┌──────────────────────────────────┐
        │  core/style_renderer.py          │
        │  markdown + style → html         │
        └──────────────┬───────────────────┘
                       │ html_content
                       ▼
        ┌──────────────────────────────────┐
        │  core/publisher.py               │
        │  save_as_draft_html(html)        │  ← 新方法，绕过 _markdown_to_html
        └──────────────────────────────────┘

   学习路径：
        URL/Image → tools/style_learner.py → analyze → styles/learned/*.yml
```

### 关键改进

1. **styles/** 目录：每个风格一个 YAML，含色号、组件 CSS、文字/段落处理规则
2. **core/style_renderer.py**：接受 `(md, style_name)` 输出 HTML，**唯一渲染入口**
3. **core/publisher.save_as_draft_html()**：新方法，绕过 `_markdown_to_html`
4. **tools/style_learner.py**：从 URL 提取 HTML → 调 LLM 分析 → 输出风格 YAML
5. **tools/style_learner_image.py**：从图片提取主色 → 生成 YAML 草案

### 发布新流程

```bash
# 列已注册风格
python3 -m core.style_renderer --list

# 用指定风格渲染
python3 -m core.style_renderer --style warm_gold --in article.md --out article.html

# 直接发布（带风格）
python3 -m core.publisher --style warm_gold --article-file article.md

# 从微信文章学习风格
python3 -m tools.style_learner --url "https://mp.weixin.qq.com/s/..." --name warm_gold

# 从图片学习
python3 -m tools.style_learner_image --image cover.png --name dark_tech
```

### 强制约束

- **AGENTS.md → styles/*.yml 单向引用**：yml 改变需文档化
- **core/style_renderer 是唯一 markdown→html 入口**：禁止直接写内联 CSS
- **core/publisher.save_as_draft_html 是唯一 HTML→微信入口**：`save_as_draft` 标记 deprecated

---

## 四、执行计划（下一步）

1. ✅ 扫描完成（本文件）
2. ⏳ 实现 `styles/warm_gold.yml`（从你给的链接学习）
3. ⏳ 实现 `core/style_renderer.py`（接受风格名渲染）
4. ⏳ 在 `core/publisher.py` 加 `save_as_draft_html()`（不再走 `_markdown_to_html`）
5. ⏳ 实现 `tools/style_learner.py`（URL → YAML）
6. ⏳ 验证：用 warm_gold 风格重新发布 创意 001，看是否一次成功

