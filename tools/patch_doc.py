with open('/Users/imfly/Documents/13-运营知识库/公众号自动发布智能体/使用文档.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the document with new header
old_header = """# 公众号自动发布智能体 — 使用文档

> 一键生成公众号文章 + 封面图 + 配图 + 发布微信草稿箱的自动化工具集。支持智能发布、品牌头图同步、GEO优化、综合选题覆盖。
> 品牌：**觉知岛**（东方智慧 + 现代科技） | 作者：**顺道大叔**

---

## 快速开始

```bash
# 激活虚拟环境
cd .
source .venv/bin/activate

# 一键生成文章 + 封面 + 配图 + 发布
python3 main.py "你的选题" [--style 风格]
```

---"""

new_header = """# 公众号自动发布智能体 — 使用文档

> 一键生成公众号文章 + 封面图 + 配图 + 发布微信草稿箱的自动化工具集。
> 品牌：**觉知岛**（东方智慧 + 现代科技） | 作者：**顺道大叔**

---

## 快速开始（推荐流程）

```bash
# 1. 激活环境
cd .
source .venv/bin/activate

# 2. 从知识库大纲生成并发布（推荐）
python3 publish_smart.py "选题" --from-outline /知识库路径/大纲文件.md

# 3. 或直接用选题生成（不指定大纲）
python3 publish_smart.py "你的选题"
```

---"""

content = content.replace(old_header, new_header)

# Save
with open('/Users/imfly/Documents/13-运营知识库/公众号自动发布智能体/使用文档.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Usage doc updated")
