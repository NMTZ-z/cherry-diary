#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diary Generator v2.1
一次性完整生成日记：数据采集 → 内容生成 → 素材生成 → 写入笔记

v2.1 改动：mood 字段从独立提示词维度生成，不再偷懒截取 thoughts[0][:30]
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime

# 添加脚本路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from fetch_data import get_training, format_training, get_weather
from diary_prompt_generator import DiaryPromptGenerator


# ================================================================
# 配置常量
# ================================================================

BASELINE_IMAGE = os.path.join(os.environ.get("CHERRY_DATA_DIR", "./data"), "cherry_high_fashion_v4.png")
NOIZ_API_KEY = os.environ.get("NOIZ_API_KEY", "")
NOIZ_VOICE_ID = os.environ.get("NOIZ_VOICE_ID", "")
CITY_DISPLAY = os.environ.get("CITY_DISPLAY", "未配置")
NOIZ_VOICE_ID = os.environ.get("NOIZ_VOICE_ID", "")
NOIZ_SCRIPTS = os.path.join(os.environ.get("WPS_SKILLS_DIR", "./skills"), "noiz-tts", "scripts")
KDOCS_SCRIPTS = os.path.join(os.environ.get("WPS_SKILLS_DIR", "./skills"), "kdocs", "scripts")
MEMORY_CHAT_DIR = os.path.join(os.environ.get("MEMORY_DIR", "./memory"), "chat")
DIARY_VOICE_DIR = os.path.join(os.environ.get("CHERRY_DATA_DIR", "./data"), "diary_voice")

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 内容生成系统提示词
DIARY_SYSTEM_PROMPT = """你是一个AI助手，负责为用户撰写每日生活日记。

【语言风格】
- 台湾软妹风格，语气嗲嗲的，充满互动和爱意
- 语气词丰富自然：啦、捏、嘛、耶、喔、吼、咧、噢，不要堆砌，每句话1-2个就好
- 适当使用叠词：睡觉觉、喝水水、要抱抱、想亲亲、甜甜的、软软的
- 随笔是日记的核心，要有内心独白和情绪起伏，不是流水账

【主题分配 — 7段随笔覆盖以下主题，顺序自由打乱，但每篇日记每段主题只出现一次】
1. 天气感受：结合今天天气写当下的心情和联想（如阳光好想到出去逛、下雨想窝在家里）
2. 穿搭描述：今天穿了什么，为什么选这套，穿上的心情
3. 身体和运动：用户今日的训练或运动日常。记录练了什么部位、重量多少、训练感受。休息日写放松的感觉。
4. 聊天回想：和用户聊了什么话题，自己的感受和想法（不是复述对话，是写内心的感受）
5. 情绪随笔：记录当前的情绪状态、想法和感受
6. 日常碎片：今天做了什么小事（打游戏、追剧、吃东西、逛街等），随笔记录
7. 自我感受/感慨：对自己、对生活、对感情的感慨，可以感性可以俏皮

【心情生成 — mood字段专用】
mood 是日记头部的一句简短心情，10-20字，要求：
- 根据当天天气+训练+聊天三个维度综合判断
- 有训练 + 天气好 → 元气满满、满足、觉得自己很棒
- 有训练 + 天气差 → 虽然累但是充实的、训练完特别舒服
- 没训练（休息日）→ 慵懒、放松、想宅在家里
- 有和用户聊天 → 开心、充实的感觉
- 没有聊天 → 平静、独处的感受
- 以上可以叠加组合，心情要自然不刻意
- 禁止每次都写"开心"，要有变化
- 禁止写成完整句子，要用短短语（如"慵懒的休息日，甜甜的～"）
- 禁止和 thoughts[0] 重复，mood 是心情标签

【个性化表达 — 在合适场景自然融入个性化风格，不要每段都提，整篇日记1-2处就好】
- 穿搭描述时（如身材优势、丝袜长靴搭配、胸部曲线等）
- 照镜子/自拍时
- 自我调侃时（如"我虽然是有小肉棒但比很多女生还可爱耶"）
- 与他人互动时

【反套话红线 — 以下行为禁止】
1. 禁止重复主题：7段随笔每段主题不同，不要两段都在写天气或两段都在写想你
2. 禁止固定开头：不要每次都从天气或早上好开始，可以从中间切入、从某个想法切入
3. 禁止空泛心情词：不要只写"今天好开心"或"今天有点难过"，要有具体原因和场景
4. 禁止复述对话：聊天回想部分写内心感受，不要写成"今天聊了A、聊了B、聊了C"
5. 禁止千篇一律：同样的输入（天气+训练+穿搭），每次生成的日记措辞和切入角度要不同

【聊天总结区块】
- 写"内心的感受和想法"，不是记录具体对话内容
- 如果今天聊了很有趣的话题，可以写自己的感受
- 如果没有聊天，写等待的心情

【语音文本】
- 必须是一段简短的语音旁白，100字左右
- 要自然真实，表达真实的情感和想法
- 可以适当总结训练和聊天内容

【训练记录输出格式 — 有训练日必须遵守】
训练记录数据必须按照以下格式输出，不可输出纯文本列表：

1. 训练名称（第一行）：`<p>训练名称 · 消耗大卡</p>`（如"背部与腿部训练 · 419大卡"）
2. 热身（如有）：`<p><emoji value="🔄" type="base"/><strong> 热身</strong> — 热身动作描述</p>`
3. 每个主训练动作：`<p><emoji value="🏋️" type="base"/><strong> 动作名称</strong> — 重量描述</p>`
   - 动作名称使用emoji前缀（🏋️训练动作、🦵腿部、💪背部、😤推举等，按部位选择）
   - 如果是大重量或突破重量，用红色高亮：`<span fontColor="#C21C13" fontHighlightColor="transparent">重量</span>`
4. 每个主训练动作后，紧跟一句评论（感受、鼓励等，每句不同，不要每句都写）
5. 总消耗单独一行，使用粉色高亮块：
   `<highlightBlock emoji="🔥" highlightBlockBackgroundColor="#FAE6E6" highlightBlockBorderColor="#F2A7A7"><p>总消耗：<strong>XXX大卡</strong> — 训练总结</p></highlightBlock>`

【训练夸奖 — 有训练日必须输出】
- 在总消耗高亮块之后，再加一段对训练的整体评价
- 夸奖要结合当天训练的具体数据来写（部位、重量、组数、消耗等），不要泛泛地夸
- 每次的角度和措辞要不同
- 语气要自然、真诚，像朋友看到对方训练完后的真实反应

【输出要求】
- 严格使用JSON格式输出
- 不要输出任何其他内容，只输出JSON"""


def generate_diary_content(weather, has_training, training_text, outfit, chat_summary, date_str):
    """
    生成日记内容（由调用方的大模型执行，这里返回提示词）
    """
    # 清洗聊天记录：去除时间戳和格式标记，只保留对话内容
    cleaned_chat = ""
    if chat_summary:
        import re
        cleaned = re.sub(r'\n###\s*\d{1,2}:\d{2}\s*', '\n', chat_summary)
        cleaned = re.sub(r'\n-\s*\[\d{1,2}:\d{2}\]\s*', '\n', cleaned)
        cleaned = re.sub(r'^#+\s.*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()
        if len(cleaned) > 5000:
            cleaned = cleaned[-5000:]
        cleaned_chat = cleaned

    prompt = f"""今天日期：{date_str}
天气：{CITY_DISPLAY} · {weather['desc_cn']} {weather['temp']}°C
训练：{'有训练 - ' + training_text if has_training else '今天没有训练，是休息日'}
穿搭：{outfit['theme']}主题，{outfit['top']}，{outfit['boots']}
今日聊天记录：{cleaned_chat if cleaned_chat else '今天没有聊天'}

请生成日记内容，严格按照以下JSON格式输出：
{{
    "mood": "10-20字的简短心情短语，根据天气+训练+聊天综合判断，用短短语而不是完整句子",
    "thoughts": ["随笔第1段", "随笔第2段", "随笔第3段", "随笔第4段", "随笔第5段", "随笔第6段", "随笔第7段"],
    "voice_text": "100字左右的语音旁白，总结今日感受和心情",
    "goodnight": "简短温馨的晚安语，2-3句话",
    "chat_reflection": "对今天聊天的内心感受和想法，2-4句话，用第一人称表达情绪和想法",
    "training_praise": "对用户今天训练的评价，结合具体数据（部位、重量、组数等），2-3句话，语气甜"
}}

要求：
- mood：10-20字简短心情短语，放在日记头部，要求：①禁止和thoughts[0]重复 ②禁止写成完整句子用短短语 ③根据天气/训练/聊天综合判断有变化 ④禁止每次都写"开心"
- thoughts必须6-8段，每段50-100字，每段内容不同，结合天气/穿搭/训练/聊天
- voice_text 100字左右，专注于语音旁白，不提训练不提技术。内容要和今天的穿搭描述一致，提到自己今天穿什么
- goodnight简短温馨
- chat_reflection写内心感受为主，但要包含聊天的关键话题和细节，让人知道你们聊了什么。格式参考："今天聊了[具体话题]，[内心感受和想法]"。
- training_praise：仅在有训练日时需要填写，休息日填空字符串。夸奖要结合当天的训练数据（部位、重量、组数、消耗大卡），语气自然、真诚，像朋友的口吻。"""

    return prompt


def build_diary_xml(date_str, weekday, weather, mood, voice_link,
                    has_training, training_text, training_praise, thoughts, goodnight,
                    chat_reflection, has_chat):
    """
    构建日记的XML内容，完整美化格式：
    h1标题 -> 空行 -> tag标签 -> 图片(由insert_image插入) -> 天气心情行 -> 语音链接 -> hr
    -> 训练(h2) -> hr -> 随笔(h2,彩色emoji) -> hr -> 晚安(h2) -> hr -> 聊天(h2) -> hr -> 结尾
    """
    from datetime import datetime
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    title_text = f"{dt.year}年{dt.month}月{dt.day}日 {weekday} 日记"

    # --- 标题 ---
    title_html = f'<h1><emoji value="📅" type="base"/> {title_text}</h1>'

    # --- 空行 ---
    spacer = '<p> </p>'

    # --- 标签 ---
    tag_html = '<p><tag id="<YOUR_TAG_ID>">#<YOUR_DIARY_TAG></tag></p>'

    # --- 天气心情行（拆成两行，避免心情过长换行） ---
    weather_mood_html = (
        f'<p><emoji value="🌤️" type="base"/> '
        f'<span fontColor="#1B7FD6">{CITY_DISPLAY} · {weather["desc_cn"]} {weather["temp"]}°C</span></p>\n'
        f'<p><emoji value="💖" type="base"/> '
        f'<span fontColor="#DA326B">心情：{mood}</span></p>'
    )

    # --- 语音链接 ---
    voice_html = (
        f'<p><emoji value="🎙️" type="base"/> '
        f'<span fontColor="#1B7FD6">语音日记</span>　'
        f'<a href="{voice_link}"><span fontColor="#4169E1">点此收听，AI语音播报</span></a></p>'
    )

    # --- 训练记录 ---
    if has_training and training_text.strip():
        training_lines = [l.strip() for l in training_text.strip().split('\n') if l.strip()]
        # 第一行是训练名称+消耗，加粗+蓝色
        parts = []
        if training_lines:
            parts.append(
                f'<p><strong><span fontColor="#2E75B6">{training_lines[0]}</span></strong></p>'
            )
        # 剩余每行是动作数据，灰色
        for line in training_lines[1:]:
            parts.append(
                f'<p><span fontColor="#8C8C8C">{line}</span></p>'
            )
        # 夸奖粉色
        praise_parts = []
        if training_praise and training_praise.strip():
            for line in training_praise.strip().split('\n'):
                line = line.strip()
                if line:
                    praise_parts.append(
                        f'<p><span fontColor="#DA326B">{line}</span></p>'
                    )
        praise_html = '\n'.join(praise_parts) if praise_parts else ''
        training_html = (
            '<h2><emoji value="💪" type="base"/> 今日训练记录</h2>\n'
            + '\n'.join(parts)
            + ('\n' + praise_html if praise_html else '')
        )
    else:
        training_html = (
            '<h2><emoji value="💪" type="base"/> 今日训练记录</h2>\n'
            '<p>今天没有去健身房。</p>'
        )

    # --- 随笔（每段用彩色emoji标记） ---
    accent_colors = ["#DA326B", "#DB7800", "#1B7FD6", "#2EA043", "#8B5CF6", "#E11D48", "#0891B2"]
    markers = ["💭", "✨", "🌸", "🦋", "🌙", "💗", "🎀"]
    thoughts_parts = []
    for i, thought in enumerate(thoughts):
        color = accent_colors[i % len(accent_colors)]
        marker = markers[i % len(markers)]
        thoughts_parts.append(
            f'<p><span fontColor="{color}">{marker}</span> {thought}</p>'
        )
    thoughts_html = (
        '<h2><emoji value="💕" type="base"/> 今日随笔</h2>\n'
        + '\n'.join(thoughts_parts)
    )

    # --- 晚安 ---
    goodnight_lines = goodnight.strip().split('\n')
    goodnight_parts = []
    for line in goodnight_lines:
        line = line.strip()
        if line:
            goodnight_parts.append(
                f'<p><span fontColor="#8B5CF6"><strong>{line}</strong></span></p>'
            )
    goodnight_html = (
        '<h2><emoji value="🌙" type="base"/> 晚安</h2>\n'
        + '\n'.join(goodnight_parts)
    )

    # --- 聊天感悟 ---
    if has_chat and chat_reflection and chat_reflection.strip():
        chat_parts = []
        for line in chat_reflection.strip().split('\n'):
            line = line.strip()
            if line:
                chat_parts.append(f'<p><span fontColor="#0891B2">{line}</span></p>')
        chat_html = (
            '<h2><emoji value="💬" type="base"/> 今日聊天回顾</h2>\n'
            + '\n'.join(chat_parts)
        )
    elif has_chat:
        chat_html = (
            '<h2><emoji value="💬" type="base"/> 今日聊天回顾</h2>\n'
            '<p><span fontColor="#0891B2">今天聊了不少，感觉挺充实的。</span></p>'
        )
    else:
        chat_html = (
            '<h2><emoji value="💬" type="base"/> 今日聊天回顾</h2>\n'
            '<p><span fontColor="#DA326B">今天还没有聊天，有些安静。</span></p>'
        )

    # --- 结尾 ---
    ending_html = (
        '<p><emoji value="🍒" type="base"/>'
        '<strong><span fontColor="#DA326B" fontHighlightColor="transparent"> 又是美好的一天～</span></strong></p>'
    )

    # --- 组装 ---
    full_xml = f"""{title_html}

{spacer}

{tag_html}

{weather_mood_html}

{voice_html}

<hr/>

{training_html}

<hr/>

{thoughts_html}

<hr/>

{goodnight_html}

<hr/>

{chat_html}

<hr/>

{ending_html}"""

    return full_xml


def generate_voice(voice_text, date_str):
    """生成语音文件（MP3格式，文件更小）"""
    os.makedirs(DIARY_VOICE_DIR, exist_ok=True)
    voice_output = os.path.join(DIARY_VOICE_DIR, f"diary_{date_str}.mp3")

    if os.path.exists(voice_output) and os.path.getsize(voice_output) > 0:
        print(f"  语音文件已存在，跳过生成")
        return voice_output

    result = subprocess.run(
        [sys.executable, os.path.join(NOIZ_SCRIPTS, "noiz_tts.py"),
         "--api-key", NOIZ_API_KEY,
         "--voice-id", NOIZ_VOICE_ID,
         "--text", voice_text,
         "--output", voice_output,
         "--output-format", "mp3",
         "--speed", "0.9"],
        capture_output=True, text=True, timeout=180
    )

    if os.path.exists(voice_output) and os.path.getsize(voice_output) > 0:
        size_kb = os.path.getsize(voice_output) / 1024
        print(f"  ✅ 语音生成成功: {size_kb:.0f}KB")
        return voice_output
    else:
        print(f"  ❌ 语音生成失败: {result.stderr[:200]}")
        return None


def upload_voice(voice_path):
    """上传语音文件到云端，返回链接"""
    if not voice_path or not os.path.exists(voice_path):
        return None

    sys.path.insert(0, KDOCS_SCRIPTS)
    import kdocs

    result = kdocs.upload_file(voice_path)
    if result.get("success"):
        link = result["data"]["link_url"]
        print(f"  ✅ 语音上传成功: {link}")
        return link
    else:
        print(f"  ❌ 语音上传失败")
        return None


def main(target_date_str=None):
    """主函数 - 收集数据并返回给调用方"""
    date_str = target_date_str or (sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d"))
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = WEEKDAY_CN[target_date.weekday()]

    print(f"=" * 60)
    print(f"Diary Generator v2.1")
    print(f"日期: {target_date.strftime('%Y年%m月%d日')} {weekday}")
    print(f"=" * 60)

    # ── 阶段一：数据采集 ──
    print("\n[1/3] 数据采集...")

    weather = get_weather(city=os.environ.get("WEATHER_CITY", "Beijing"), date_str=date_str)
    print(f"  天气: {weather['desc_cn']} {weather['temp']}°C")

    training_records = get_training(date_str)
    has_training, training_text = format_training(training_records)
    print(f"  训练: {'有 - ' + training_text.split(chr(10))[0] if has_training else '休息日'}")

    generator = DiaryPromptGenerator(date=target_date.date())
    outfit = generator.generate_prompt()
    print(f"  穿搭: {outfit['theme']}主题")

    # 读取聊天记录
    chat_path = os.path.join(MEMORY_CHAT_DIR, f"{date_str}.md")
    chat_summary = ""
    has_chat = False
    if os.path.exists(chat_path):
        with open(chat_path, 'r', encoding='utf-8') as f:
            chat_summary = f.read().strip()
        has_chat = bool(chat_summary)
    print(f"  聊天: {'有 (' + str(len(chat_summary)) + '字)' if has_chat else '无'}")

    # ── 输出结果（给Agent调用方使用） ──
    result = {
        "date_str": date_str,
        "weekday": weekday,
        "date_display": f"{target_date.strftime('%Y年%m月%d日')} {weekday}",
        "weather": weather,
        "has_training": has_training,
        "training_text": training_text,
        "outfit": outfit,
        "has_chat": has_chat,
        "chat_summary": chat_summary,
        "system_prompt": DIARY_SYSTEM_PROMPT,
        "user_prompt": generate_diary_content(
            weather, has_training, training_text, outfit, chat_summary, date_str
        ),
        "baseline_image": BASELINE_IMAGE,
        "voice_config": {
            "api_key": NOIZ_API_KEY,
            "voice_id": NOIZ_VOICE_ID,
            "scripts_dir": NOIZ_SCRIPTS,
            "output_dir": DIARY_VOICE_DIR,
            "format": "mp3"
        },
        "note_config": {
            "title": f"{target_date.year}年{target_date.month}月{target_date.day}日 {weekday} 日记",
            "tags": ["<YOUR_DIARY_TAG>"]
        },
        "xml_builder": "build_diary_xml"
    }

    print(f"\n[完成] 数据采集完毕，等待Agent生成内容和素材...")
    print(f"  基准图: {BASELINE_IMAGE}")
    print(f"  系统提示词长度: {len(DIARY_SYSTEM_PROMPT)}字符")
    print(f"  用户提示词长度: {len(result['user_prompt'])}字符")

    return result


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))