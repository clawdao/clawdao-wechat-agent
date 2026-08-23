"""AI 文章生成模块 - 调用本地 DeepSeek API 生成公众号文章（结构化版）"""
from openai import OpenAI
from config import get_api_config


def generate_article(topic: str, style: str = "轻松专业") -> str:
    api_cfg = get_api_config()
    client = OpenAI(base_url=api_cfg["base_url"], api_key=api_cfg.get("api_key", "not-needed"))

    prompt = f"""你是一个资深公众号内容创作者，精通GEO（Generative Engine Optimization，生成式引擎优化）。请根据以下选题，写一篇在AI搜索中高可见度的公众号文章。

## 核心GEO要求
- 每段融入1-2个**实体词**（具体人名/品牌名/书名/数据/概念），让AI能抓取关键实体
- 自然形成**问答模式**：在段落中嵌入「为什么…」「什么是…」句式，增加被AI搜索为直接答案的概率
- **数据锚点**：每个核心观点尽量附一个具体数据、年份或来源（如「a16z 2025年报告显示」）
- **语义层级**：H1→H2→H3层级分明，逻辑递进清晰，让AI能准确理解文章脉络
- **互链概念**：在同一主题下串联3-4个相关概念（如「无为而治」串起「AI Agent」「认知升级」「组织效率」），增加主题权威性
- 结尾用 **开放式问题** 引导互动，增加用户的停留和讨论（AI也会参考互动质量）

## 写作要求
- 选题：{topic}
- 风格：{style}
- 字数：约800-1000字（适合手机阅读，同时保证内容深度）
- 格式：Markdown

## 格式模板
# 标题：不超过60字，可以使用标点（如冒号、引号、破折号）

开篇引入（1-2句，场景化切入。用「你是不是也…」制造共鸣）

## 一、小标题用中文数字

正文段落（200-300字）。**核心观点加粗**。
每段嵌入实体词和数据锚点。
适当插入引用：

> 一句金句或名人名言，用引用格式。

## 二、第二个小标题

正文段落。**加粗关键词**。
自然融入问答模式。

---

> 结尾金句或总结，加互动引导

## GEO格式说明
- 每个小标题前用 ## 
- 重要内容用 **加粗**
- 金句/名人名言用 > 引用
- 段落之间用 --- 分隔
- 标题可以使用标点（冒号、引号、破折号等）
- 语言通俗易懂，适合手机阅读
- 每段至少包含一个具体实体词（人/品牌/数据/概念）

请直接输出文章内容：
"""
    response = client.chat.completions.create(
        model=api_cfg["chat_model"],
        messages=[
            {"role": "system", "content": "你是专业的公众号内容创作者，精通GEO（Generative Engine Optimization）。你擅长写出实体密度高、语义结构清晰、容易被AI索引和引用的文章。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=6000,
    )
    return response.choices[0].message.content


def extract_title(article: str) -> str:
    for line in article.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            return line.replace("# ", "").strip()
    return "无标题"
