# 代码整理重构计划（2026-08-21）

> 目标：将 25 个 Python 脚本按功能模块分文件夹，删除 .bak 备份，中文改英文，添加测试。

## 一、目录结构

```
公众号智能体/
├── main.py                        🚀 CLI 入口（精简后）
├── config.py                      ⚙️ 配置（保持根）
│
├── core/                          📚 核心流程（main 直接依赖）
│   ├── __init__.py
│   ├── article.py                 ← 原 article_generator.py
│   └── publisher.py               ← 原 wechat_publisher.py
│
├── covers/                        🖼️ 封面图生成
│   ├── __init__.py
│   ├── base.py                    ← 原 cover_generator.py
│   ├── deluxe.py                  ← 原 cover_deluxe.py
│   ├── lite.py                    ← 原 cover_减少依赖_deluxe.py
│   ├── themed.py                  ← 原 cover_SaaS越买越焦虑_deluxe.py
│   ├── enhanced.py                ← 原 image_generator_enhanced.py
│   ├── banner.py                  ← 原 title_banner_generator.py
│   ├── helper.py                  ← 原 aideep_cover.py
│   └── regen.py                   ← 原 regenerate_images.py
│
├── publish/                       📤 发布工具
│   ├── __init__.py
│   ├── smart.py                   ← 原 publish_smart.py（主用）
│   ├── single.py                  ← 原 publish_article.py
│   ├── batch.py                   ← 原 publish_batch.py
│   ├── final.py                   ← 原 publish_final.py
│   ├── v2.py                      ← 原 publish_v2.py（保留）
│   ├── v3.py                      ← 原 publish_v3.py（保留）
│   ├── both.py                    ← 原 publish_both_articles.py
│   └── republish.py               ← 原 republish_opd.py
│
├── tools/                         🔧 工具/集成
│   ├── __init__.py
│   ├── seedream.py                ← 原 seedream_generator.py
│   ├── opd.py                     ← 原 generate_opd.py
│   ├── fix.py                     ← 原 fix.py
│   ├── patch_doc.py               ← 原 patch_usage_doc.py
│   └── volcengine_sign.py         ← 原 test_volcengine_sign.py
│
└── tests/                         🧪 测试
    ├── __init__.py
    ├── test_config.py
    ├── test_core_article.py
    ├── test_core_publisher.py
    └── test_covers.py
```

## 二、删除文件（直接 rm）

- `cover_generator_v1.py.bak`
- `main.py.bak`
- `publish_v2.py.bak`
- `wechat_publisher_v1.py.bak`

## 三、main.py 依赖关系

```python
# 当前（main.py 头部）
from article_generator import generate_article, extract_title
from image_generator_enhanced import generate_cover_enhanced, generate_inline_image
from wechat_publisher import WeChatPublisher

# 整理后
from core.article import generate_article, extract_title
from covers.enhanced import generate_cover_enhanced, generate_inline_image
from core.publisher import WeChatPublisher
```

## 四、模块间依赖关系

| 模块 | 依赖 |
|---|---|
| `core/article.py` | `config` |
| `core/publisher.py` | `config` |
| `covers/*.py` | `config`, `core/publisher`（部分） |
| `publish/*.py` | `config`, `core/publisher`, `core/article` |
| `tools/seedream.py` | `config` |
| `tools/opd.py` | `core/article`, `core/publisher` |
| `main.py` | `core/article`, `core/publisher`, `covers/enhanced`, `tools/seedream` |

## 五、步骤

1. ✅ 删除 .bak 文件
2. 🆕 创建新目录（core/、covers/、publish/、tools/、tests/）
3. 🆕 创建各包的 __init__.py
4. 🔄 git mv 文件到新位置（保留历史）
5. 🔄 修改各文件内的 import 路径
6. 🔄 修改 main.py 的 import
7. 🧪 写基础测试
8. ✅ 验证：python3 main.py --help + 跑测试
9. 📝 更新 README

## 六、保留兼容层

为了不破坏老脚本调用，在 `tools/` 下提供 shim：

- `tools/run_main.py` → `from main import main; main()`
- 或直接在 README 写明："旧命令 `python3 cover_generator.py` 请改用 `python3 -m covers.base`"