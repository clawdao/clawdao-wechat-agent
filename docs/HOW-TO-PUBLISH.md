# 公众号发布操作指南（v2.1）

> 🎯 **目标**：拿到一篇文章（markdown 文本），就能发布到公众号草稿箱，并自动清理上一次留下的图片垃圾。
> 🧹 **承诺**：每次发布都自动清理上一次的草稿 + 封面图 + 品牌头图，公众号素材库不再堆积。

---

## 一、给 AI 助理的提示词（直接复制）

```
请把下面这篇文章发布到公众号「亿检链」草稿箱，使用 warm_gold 风格。

【清理旧资源】
- 上次草稿 media_id：<填入>
- 上次封面图 media_id：<填入>
- 上次品牌头图 media_id：<填入>
如果没有则忽略。

【文章标题】
<填入>

【正文 markdown】
<粘贴整篇文章，## 小标题、> 引用、**加粗**、![图片](路径) 都要保留>

【封面图】
请使用 images/亿检链_文章封面_900x500.png
（首次发布请先用封面生成器做一张同主题的 900×500 封面）

【品牌头图】
使用默认 images/亿检链_头图横幅_900x383.png（自动缓存复用，不要每次重传）

【执行步骤】
1. 调用 core/publish.py 完成发布
2. 记下返回的 3 个 media_id（草稿、封面、品牌头图）
3. 在 docs/HOW-TO-PUBLISH.md 末尾的「历次发布记录」追加一行
4. 把这次用到的 3 个 ID 同步到下次发布时填入「清理旧资源」
```

---

## 二、实际执行的命令（开发者参考）

### 第一次发布（无旧资源要清理）

```bash
cd /Users/imfly/projects/Agents/clawdao-wechat-agent
python3 core/publish.py \
  --style warm_gold \
  --title "你的文章标题" \
  --in path/to/article.md \
  --cover images/亿检链_文章封面_900x500.png
```

执行后会打印：

```
✅ 完成。新草稿 media_id: XXXX
   封面图 media_id: YYYY
   品牌头图 media_id: ZZZZ
   下次覆盖发布时，可用：
     --delete-old XXXX
     --delete-old-cover YYYY
     --delete-old-brand ZZZZ
```

**把 XXXX / YYYY / ZZZZ 抄到下次发布命令里**（见下面）。

### 第二次及以后发布（自动清理旧资源）

```bash
cd /Users/imfly/projects/Agents/clawdao-wechat-agent
python3 core/publish.py \
  --style warm_gold \
  --title "你的文章标题" \
  --in path/to/article.md \
  --cover images/亿检链_文章封面_900x500.png \
  --delete-old XXXX \         # 上次的草稿
  --delete-old-cover YYYY \   # 上次的封面图（永久素材）
  --delete-old-brand ZZZZ     # 上次的品牌头图（永久素材）
```

每次发布后，**把新的 3 个 ID 覆盖到上面命令里**就形成了循环。

---

## 三、它做了什么

### 自动完成的事

| 步骤 | 说明 |
|------|------|
| 1. 清理旧资源 | 删旧草稿 + 旧封面图 + 旧品牌头图（如果有传 ID 的话） |
| 2. 渲染 HTML | 按 `--style` 指定的风格渲染 markdown |
| 3. 上传内联图片 | 自动扫描 `![](path)`，上传到微信 CDN，替换为微信 URL |
| 4. 复用品牌头图 | 命中缓存时直接复用，不重传（节省微信素材额度） |
| 5. 上传封面图 | 作为 thumb_media_id（推送顶部大图） |
| 6. 生成摘要 | 从 markdown 纯文本提取，不是从 HTML 头标签取（避免 `<section>` 显示问题） |
| 7. 注入 GEO JSON-LD | 文章结构化数据，帮助 AI 搜索引擎理解 |
| 8. 推送到草稿箱 | 返回新草稿的 media_id |

### 不做的事（说明清楚）

- ❌ **正文里上传到微信 CDN 的内联图**（`uploadimg` 返回的 URL）：**无法主动删除**，微信 3 天自动回收。这是微信 API 限制。详见 FAQ。
- ❌ **自动推送**：只到草稿箱，**最终发布需要你手动在公众号后台点"群发"**（这是平台强制要求，第三方无法绕过）。
- ❌ **图片生成**：封面图 / 品牌头图是项目预置素材，不自动生成。如果要换主题封面，请先用 `tools/yijianlian_cover.py` 生成再指定路径。

---

## 四、可选：第一次完整流程（图文全流程）

### Step 1：准备封面图

```bash
# 方式 A：用项目默认封面（最快）
ls images/亿检链_文章封面_900x500.png  # 已存在

# 方式 B：生成新封面（按主题）
python3 tools/yijianlian_cover.py \
  --title "顺道大叔：一人企业的未来" \
  --subtitle "AI Native 时代的新范式" \
  --out outputs/cover_2026-10.png
```

### Step 2：准备 markdown 文章

放在 `outputs/your-article.md`，要求：
- 第 1 行 `# 标题`
- `## 小标题` 分段
- `> 引用文字` 关键金句
- `**加粗**` 强调
- `![说明](./outputs/your-image.png)` 内联图（路径相对项目根）

### Step 3：发布

```bash
python3 core/publish.py \
  --style warm_gold \
  --title "标题（≤64字）" \
  --in outputs/your-article.md \
  --cover outputs/cover_2026-10.png
```

### Step 4：打开公众号后台 → 草稿箱 → 检查并群发

URL：`https://mp.weixin.qq.com/cgi-bin/appmsg?action=list&type=10`

---

## 五、常见问题 FAQ

### Q1：为什么品牌头图不每次重传？

A：因为它是固定素材（`images/亿检链_头图横幅_900x383.png`），重复上传会浪费微信素材库额度。系统会把首次上传的 URL 和 media_id 缓存在 `outputs/.brand_header_cache.json`，下次直接复用。**只有当你换了头图文件（mtime 变了），才会重新上传。**

### Q2：为什么正文里上传的图删不掉？

A：微信 API 有两类图片：

| 类型 | 接口 | 能否主动删 |
|------|------|-----------|
| 永久素材（封面图、品牌头图） | `/material/add_material` → 返回 `media_id` | ✅ 可用 `material/del_material` 删 |
| 图文内联图 | `/media/uploadimg` → 返回 `URL` | ❌ **没有删除接口，3 天自动回收** |

所以本工具的清理只覆盖封面图和品牌头图。正文图片请节省使用（每篇建议 3-5 张内），或等微信 3 天自动回收。

### Q3：清理失败怎么办？

如果打印 `⚠️ 清理旧素材失败: {...errcode: 40007...}`，说明 media_id 不存在或已过期。直接忽略，**继续发布**就行。常见原因：
- 上次发布的草稿已经被手动删除（前端操作）
- 旧封面图已经超过 7 天未引用（微信会自动清理）

### Q4：能不能批量发布多篇？

可以写个 shell 循环，或者用 `publish/batch.py`（如果你需要的话）：

```bash
for md in outputs/article-*.md; do
  python3 core/publish.py --style warm_gold --title "..." --in "$md" ...
done
```

### Q5：我换风格怎么办？

```bash
python3 core/publish.py --list-styles  # 列出所有风格
# 选择一个，比如 warm_gold_v2
python3 core/publish.py --style warm_gold_v2 ...
```

要学新风格：`python3 tools/style_learner.py --url <微信文章链接>`

---

## 六、历次发布记录

> 每次发布后，把返回的 3 个 ID 记录在下面，下一次发布时填入"清理旧资源"。

| 日期 | 标题 | 草稿 media_id | 封面图 media_id | 品牌头图 media_id | 状态 |
|------|------|---------------|------------------|-------------------|------|
| 2026-10-01 | 测试：publish 端到端验证 | `bLecvU4Iq3PpzwzL_6k_RtTsRtLVLkRhjuOM97JyTGyB0mQFyBmTveSrOvwnXBb3` | `bLecvU4Iq3PpzwzL_6k_RtEpFn7nlb2f9Ij-rOWc4rKhIFhCBHbCXljRLRHXHmcC` | `bLecvU4Iq3PpzwzL_6k_RkQL8MUByavlt5UP_lQbuABMleJzGl1MYu8lu4xDWEx1` | ✅ |
| 2026-10-01 | 如果软件没有天花板：ClawDao「项目即一等公民」设计哲学 | `bLecvU4Iq3PpzwzL_6k_Rlp0U0TXY8EBPOvP7aTL0X55fKjLJD3hOLINlVKiRvT6` | `bLecvU4Iq3PpzwzL_6k_Rg9fUUbqfNz_Qq_gJA7oBkmoHt3ypG4it9ty2cy0i6yA` | `bLecvU4Iq3PpzwzL_6k_Rv0lCbYgyf5DqUscyBSkR3jZlk60cu4PenWIizqcL19h` | ✅ |
| 2026-10-01 | 一个人，一篇文章，一杯深夜咖啡（重建等价完整版） | `bLecvU4Iq3PpzwzL_6k_RpWI4UJiCoEMKc_61tvvDXMBItgGSGTsCKgq8RA5p7Uq` | `bLecvU4Iq3PpzwzL_6k_RpeTmv0y_YJi67fjtPGg6O13DlnAig1eTOXoxca1Bmjk` | `bLecvU4Iq3PpzwzL_6k_Rv0lCbYgyf5DqUscyBSkR3jZlk60cu4PenWIizqcL19h`（缓存命中，物理素材已于本次清理） | ✅ |
