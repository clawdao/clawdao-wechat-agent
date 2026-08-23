"""OPD系列文章批量生成 & 发布"""
import json
import os
from openai import OpenAI
from config import get_api_config
from core.article import extract_title
from covers.base import generate_cover
from core.publisher import WeChatPublisher

api_cfg = get_api_config()
client = OpenAI(base_url=api_cfg["base_url"], api_key=api_cfg.get("api_key", "not-needed"))

TOPICS = [
    {
        "id": "01",
        "angle": "认知颠覆",
        "hook_engine": "反共识断言型",
        "title_hint": "「你以为创业第一步是注册公司，其实OPD才是标准答案」",
        "reader": "副业型（30岁白领副业党）",
        "emotion": "恐惧 + 好奇",
        "dna_focus": "OPD / 管理系统+知识系统 / 顺道而为 / OPC对照",
    },
    {
        "id": "02",
        "angle": "趋势风口",
        "hook_engine": "颠覆+时代型",
        "title_hint": "「OPC已死，OPD当立：AI Agent时代的个体组织革命」",
        "reader": "技术型（程序员/独立开发者）",
        "emotion": "野心 + 好奇",
        "dna_focus": "OPD / 产品系统+交易系统 / 顺道而为 / 四系统",
    },
    {
        "id": "03",
        "angle": "工具实操",
        "hook_engine": "悬念清单型",
        "title_hint": "「顺道而为的人都有这3个共同点」",
        "reader": "转型型（35+被优化的管理者）",
        "emotion": "共鸣 + 野心 + 怀疑",
        "dna_focus": "OPD / 四系统全覆盖 / 顺道而为 / OPC对照",
    },
]

def generate_article(topic_info):
    prompt = f"""你是一位中文公众号主理人型爆款作者，连续写作10年。

写一篇文章，选题信息如下：

## 选题信息
- 选题角度：{topic_info['angle']}
- 核心断言：{topic_info['title_hint']}
- 目标读者：{topic_info['reader']}
- 情感触发器：{topic_info['emotion']}
- 钩子引擎：{topic_info['hook_engine']}
- DNA主轴：{topic_info['dna_focus']}

## 强制文章结构
[Hook §] ≤300字 反常识开场，第一段必须出现一个具体数字或场景
[Pain §] 500-600字 拆旧认知/旧痛点
[Lens §] 800-1200字 重塑新认知，植入OPD/四系统/顺道而为
[Action §] 500-700字 可执行抓手
[Close §] 150-250字 可截图传播的金句收尾

## 风格强制规则
- 单句成段占比 ≥30%
- 段落不超过3行
- 金句密度 ≥5/千字
- 全文禁用词：赋能、底层逻辑、闭环、抓手、赛道、内卷、躺平、焦虑、破局、降维打击、心法、思维模型、认知升级
- 数字密度：每篇出现具体数字 ≥4处
- 关键词密度：OPD ≥6次、四系统明称≥8次、顺道而为≥3次、OPC≥3次
- 不出现「首先/其次/再次/最后」
- 任何抽象概念必须配具体场景
- 全文2500-3000字

直接输出文章正文，不要额外说明。"""

    response = client.chat.completions.create(
        model=api_cfg["chat_model"],
        messages=[
            {"role": "system", "content": "你是专业公众号主理人型作者，文风冷、静、有金句，类似界面故事与刘润的混合体。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=4000,
    )
    article = response.choices[0].message.content

    # 如果不够长，补充生成后续部分
    if len(article) < 2200:
        repair_prompt = f"""继续补充上文未完成的部分，保持风格一致，接续上文逻辑继续写至少800字。

上文截止部分：
{article[-500:]}

直接继续输出内容，不要重复标题。"""
        response2 = client.chat.completions.create(
            model=api_cfg["chat_model"],
            messages=[
                {"role": "system", "content": "你正是上文作者，保持风格继续写作。"},
                {"role": "user", "content": repair_prompt},
            ],
            temperature=0.8,
            max_tokens=2000,
        )
        article += "\n\n" + response2.choices[0].message.content

    return article

def clean_for_title(text, max_chars=60):
    """清理标题用于发布"""
    title = extract_title(text) or "OPD系列文章"
    # 只去除不能出现在标题中的特殊字符
    for ch in ['"', '"', "'", "'"]:
        title = title.replace(ch, '')
    if len(title) > max_chars:
        title = title[:max_chars]
    return title

def publish_article(article, cover_path=None):
    """发布单篇文章到公众号草稿箱"""
    publisher = WeChatPublisher()
    title = clean_for_title(article)
    success = publisher.save_as_draft(
        title=title,
        content=article,
        cover_image_path=str(cover_path) if cover_path else None,
    )
    return success

# === 主流程 ===
for topic in TOPICS:
    print(f"\n{'='*50}")
    print(f"【第{topic['id']}篇】{topic['angle']} | {topic['title_hint'][:30]}...")
    print(f"{'='*50}")

    print(f"🤖 正在生成文章...")
    article = generate_article(topic)
    print(f"✅ 文章生成完毕，字数：{len(article)}")

    # 保存
    out_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"article_opd_{topic['id']}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(article)
    print(f"💾 已保存: {path}")

    # 生成封面
    title_line = clean_for_title(article)
    print(f"🎨 正在生成封面...")
    cover_path = generate_cover(title_line, topic['angle'])
    print(f"✅ 封面已生成: {cover_path}")

    # 发布
    print(f"📤 正在发布到公众号草稿箱...")
    success = publish_article(article, cover_path)
    if success:
        print(f"✅ 第{topic['id']}篇发布成功！")
    else:
        print(f"⚠️ 第{topic['id']}篇发布失败")

print(f"\n{'='*50}")
print("🎉 全部完成！三篇文章已生成并发布。")
