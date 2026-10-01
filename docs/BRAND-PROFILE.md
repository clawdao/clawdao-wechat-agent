# 品牌档案机制（brand_profile.yml）

> 让一个项目服务多个公众号用户。每个公众号的个性化信息集中在一个 yml 里，运营者可改、可重置、可分发。

---

## 一、为什么需要它？

之前项目里到处是硬编码：
- `core/publish.py` 里写着 `"author": "顺道大叔"`
- `core/publisher.py` 里也是 `"name": "顺道大叔"`
- 默认头图路径 `images/亿检链_头图横幅_900x383.png`
- 默认风格 `tech_blue` / `warm_gold`

**问题**：另一个公众号用户想用这个工具，必须改源码。改完自己也乱。

**解法**：把"公众号个性化信息"抽出来，变成 `brand_profile.yml`。代码只读它，不再硬编码。

---

## 二、个性化 vs 风格化（关键区分）

| 文件 | 角色 | 谁关心 |
|------|------|--------|
| `brand_profile.yml` | **公众号个性化**：你是谁、母品牌、作者、slogan、品牌资产路径、品牌色 | 每个公众号用户不同 |
| `styles/*.yml` | **美学风格**：暖金色 / 科技蓝 / 禅意风……配色和排版组件 | 任何公众号都可复用 |

风格被多个品牌复用；个性化是品牌独有的。两者解耦后：

- 你换品牌（公众号改名）：只改 `brand_profile.yml`
- 你换风格（想试科技蓝）：只换 `styles/*.yml` 或传 `--style tech_blue`
- 你换作者署名：只改 `brand_profile.yml` 的 `author.name`

---

## 三、首次使用

```bash
python3 tools/profile_setup.py
```

启动 8 个简短问题的访谈（约 1 分钟）：

```
【1/8】公众号名（中文）
  💡 出现在文章标题下方、署名、封面图水印
  默认：亿检链
  你的回答（回车用默认）> __

【2/8】公众号英文名 / 缩写
  💡 用于 LOGO、域名、英文场景
  默认：LIMSCHAIN
  你的回答（回车用默认）> __

【3/8】母品牌 / 所属公司
  💡 可填：某某公司旗下 / 个人 IP / 无
  默认：利姆斯科技旗下品牌
  ...

【4/8】一句话定位（slogan）
  💡 整篇文章围绕它展开，建议 8-15 字
  默认：让企业运营可被验证
  ...
```

按 Enter = 用默认；输内容 = 自定义。生成 `brand_profile.yml`。

### 查看当前

```bash
python3 tools/profile_setup.py --show
```

输出：
```
=== 当前 brand_profile.yml ===
账号     : 亿检链 (LIMSCHAIN)
母品牌   : 利姆斯科技旗下品牌
Slogan   : 让企业运营可被验证
内容领域 : 科技 · 商业 · 认知
作者     : 顺道大叔
风格     : warm_gold
品牌头图 : images/亿检链_头图横幅_900x383.png
作者签名 : 愿你的下一篇文章，写得比今天更轻松一点
```

### 重新生成

```bash
python3 tools/profile_setup.py --reset
```

会自动备份当前的 `brand_profile.yml` 到 `brand_profile.yml.bak`。

---

## 四、profile 结构

```yaml
profile:
  # ── 基本信息 ──
  account:
    name: "亿检链"                  # 公众号名
    name_en: "LIMSCHAIN"            # 英文名
    parent_brand: "利姆斯科技旗下品牌"
    slogan: "让企业运营可被验证"
    domain: "科技 · 商业 · 认知"     # 内容领域标签
    audience: "科技从业者、创业者、..."  # 目标读者

  # ── 作者信息 ──
  author:
    name: "顺道大叔"
    signature: "愿你的下一篇文章，写得比今天更轻松一点"
    voice: "轻松专业，有深度但不晦涩"

  # ── 品牌资产 ──
  brand_assets:
    cover_image: "images/亿检链_文章封面_900x500.png"
    brand_header: "images/亿检链_头图横幅_900x383.png"
    square_share: "images/亿检链_分享小图_500x500.png"
    official_header: "images/亿检链_头图横幅_官方_1600x640.png"

  # ── 品牌色 ──
  colors:
    primary: "#0a2e7a"
    primary_alt: "#1e6dff"
    accent: "#f24c3a"
    text: "#333333"
    text_muted: "#888888"

  # ── 微信配置 ──
  wechat:
    default_style: "warm_gold"
    default_author: "顺道大叔"
    cover_width: 900
    cover_height: 500
    brand_header_width: 900
    brand_header_height: 383

  # ── GEO 配置 ──
  geo:
    publisher_name: "亿检链"
    publisher_description: "东方智慧 + 现代科技，AI时代的认知升级平台"
    publisher_type: "Organization"
```

---

## 五、代码里如何读取

```python
from brand_profile import account, author, brand_assets, colors, wechat, geo

print(account()["name"])             # "亿检链"
print(author()["name"])              # "顺道大叔"
print(brand_assets()["brand_header"])  # "images/亿检链_头图横幅_900x383.png"
print(wechat()["default_style"])     # "warm_gold"
```

也可以获取完整 dict：

```python
from brand_profile import get_profile
profile = get_profile()
```

---

## 六、迁移路径（已做的部分）

| 文件 | 改动 |
|------|------|
| `brand_profile.yml` | 🆕 新增：集中所有个性化信息 |
| `brand_profile.py` | 🆕 新增：Python 加载器（带默认 fallback） |
| `tools/profile_setup.py` | 🆕 新增：8 题访谈式采集工具 |
| `core/publish.py` | ✅ 改：`author` 字段、`style_name` 默认值、默认头图路径 → 全部从 profile 读 |

未来可以继续迁移：
- `core/publisher.py`：JSON-LD 里的 `name: "顺道大叔"`、`publisher.name: "亿检链"` 改为读 profile
- `tools/yijianlian_cover.py`：封面生成器里的 `BRAND_NAME = "亿检链"` 改为读 profile
- `tools/yijianlian_inline.py`：插图生成器里的硬编码改为读 profile

---

## 七、FAQ

### Q1：profile 改完后代码不生效？
A：在 Python 里 profile 是带缓存的。如果改了 yml 但代码没读到新值，**重启进程**或调用 `brand_profile.reset_cache()`。

### Q2：可以一个项目多公众号吗？
A：可以。运行 `python3 tools/profile_setup.py --reset` 重置，把生成的 `brand_profile.yml` 复制成多个版本（如 `brand_profile_品牌A.yml`），需要切换时手动覆盖或在代码里传入 path。

### Q3：profile 找不到时怎么办？
A：`brand_profile.py` 自带默认 dict，yml 不存在也能跑，行为和硬编码时一致。**完全向后兼容。**
