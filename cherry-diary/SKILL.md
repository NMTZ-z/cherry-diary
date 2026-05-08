---
name: cherry-diary
description: 每日日记生成。当用户要求"写日记"、"生成日记"、"今日日记"、"cherry diary"时触发。自动采集真实天气、训练数据，生成图片和语音，写入WPS笔记。
---

# 每日日记

每天生成一篇图文并茂的语音日记，写入 WPS 笔记。

## 技术资源

| 文件 | 用途 |
|------|------|
| `scripts/main.py` | 数据采集 + 提示词构建 + XML构建器 |
| `scripts/ainote_mcp.py` | MCP客户端：创建笔记、写入内容、插入图片 |
| `scripts/fetch_data.py` | 训练数据 + 天气数据（wttr.in，自动缓存） |
| `scripts/diary_prompt_generator.py` | 穿搭随机生成器（v5.0，中等幅度表情 + 眼神交互） |
| 基准图 `<DATA_DIR>/cherry_high_fashion_v4.png` | 图片生成参考（必须使用） |

## 执行流程（Agent一次性完成）

### 步骤1：数据采集

    import sys
    sys.path.insert(0, os.path.join(os.environ.get("WPS_SKILLS_DIR", "./skills"), "cherry-diary", "scripts"))
    from main import main, build_diary_xml

    data = main("2026-04-17")  # 传入目标日期字符串

`data` 返回字段：
- `weather`（含 desc_cn、temp） / `has_training` / `training_text` / `outfit`（含 prompt） / `has_chat` / `chat_summary`
- `system_prompt` / `user_prompt`（AI内容生成的提示词，已注入写作规则）
- `baseline_image` / `note_config`（含 title） / `voice_config`

### 步骤2：AI内容生成

使用 `data["system_prompt"]` 和 `data["user_prompt"]` 生成JSON：

    {
      "mood": "10-20字简短心情短语",
      "thoughts": ["随笔1", "随笔2", ..., "随笔6~8段"],
      "voice_text": "100字语音旁白",
      "goodnight": "2-3句晚安语",
      "chat_reflection": "2-4句聊天内心感悟",
      "training_praise": "训练夸奖（休息日填空字符串）"
    }

规则：
- **`mood` 必须从JSON中取出，直接传入 `build_diary_xml`**。禁止截取 thoughts[0] 凑数！mood 是独立字段，10-20字短短语，根据天气+训练+聊天综合判断
- `thoughts` 每段50-100字，结合天气/穿搭/训练/聊天，**不重复主题**
- `chat_reflection` 写内心感受，不写技术细节（不提"记忆系统""bug"等词）
- `voice_text` 专注情话，不提训练和技术

### 步骤3：生成图片

**严格规则（违反会导致生成质量下降）：**

1. **基准图**：必须使用 `cherry_high_fashion_v4.png`（data["baseline_image"]），这是唯一正确的基准图
2. **参考权重**：使用 `data["outfit"]["ref_weight"]`（默认 0.85），由脚本自动生成，直接使用即可
3. **Prompt 语言**：全英文，**绝对禁止**在 prompt 中添加任何中文内容
4. **相机参数**：**绝对禁止**添加相机型号/镜头参数（Canon/85mm/f/1.4 等），会导致生成质量下降
5. **禁止否定描述**：**绝对禁止**在 prompt 中写 `no`、`without`、`avoid` 等否定词（如 `no lip deformation`、`no extra limbs`），会导致不可预测的结构错误
6. **禁止修改 Prompt**：**绝对不要**修改 `data["outfit"]["prompt"]` 的内容，脚本 v5.0 已内置以下优化：
   - 自然语言连贯段落（非关键词拼接）
   - 低角度仰拍全身构图（横屏 16:9 全身入镜）
   - 因果式曲线描述 + 衣服贴合度暗示（强化大胸表现）
   - 光线描述含光源方向和光影效果
   - 嘴唇安全约束（`Soft natural lips` 独立轻量约束，无否定描述）
   - 中等幅度表情变化（20条表情库，每条15-25词，不抢构图注意力）
   - 眼神交互融入每条表情（`eyes on camera` 变体）
   - 精选质感修饰词（写实感 + 背景虚化 + 色彩锚定）

    generate_image(
        prompt=data["outfit"]["prompt"],
        input_images=[{"type": "path", "path": data["baseline_image"], "weight": data["outfit"]["ref_weight"]}],
        aspect_ratio="16:9"
    )

### 步骤4：生成语音（MP3）并上传

    import subprocess, sys
    output = f"<DATA_DIR>/diary_voice/diary_{date}.mp3'date_str']}.mp3"

    subprocess.run([
        sys.executable,
        os.path.join(os.environ.get("WPS_SKILLS_DIR", "./skills"), "noiz-tts", "scripts", "noiz_tts.py"),
        "--api-key", os.environ.get("NOIZ_API_KEY", ""),
        "--voice-id", "<YOUR_NOIZ_VOICE_ID>",
        "--text", voice_text,
        "--output", output,
        "--output-format", "mp3",
        "--speed", "0.9"
    ], capture_output=True, text=True, timeout=180)

    # 上传语音
    sys.path.insert(0, os.path.join(os.environ.get("WPS_SKILLS_DIR", "./skills"), "kdocs", "scripts"))
    import kdocs
    result = kdocs.upload_file(output)
    voice_link = result["data"]["link_url"]

### 步骤5：构建XML并写入新笔记

**重要**：不要在已有笔记上更新（replace会导致内容重复），必须创建新笔记。

    from ainote_mcp import AinoteMCPClient

    xml_content = build_diary_xml(
        date_str=data["date_str"],
        weekday=data["weekday"],
        weather=data["weather"],
        mood=diary_content["mood"],  # 从JSON的mood字段取，禁止截取thoughts[0]
        voice_link=voice_link,
        has_training=data["has_training"],
        training_text=data["training_text"],
        training_praise=diary_content["training_praise"],
        thoughts=thoughts,
        goodnight=goodnight,
        chat_reflection=chat_reflection,
        has_chat=data["has_chat"]
    )

    client = AinoteMCPClient()
    client.initialize()
    note_id = client.create_note(data["note_config"]["title"])
    client.replace_first_block(note_id, xml_content)

    # 注意：replace后block_id会变，需要重新获取outline
    outline = client._call("get_note_outline", {"note_id": note_id})
    outline_data = json.loads(client._get_text(outline))
    heading_id = outline_data["blocks"][0]["id"]

    client._call("insert_image", {
        "note_id": note_id,
        "anchor_id": heading_id,
        "position": "after",
        "src": image_url,
    })
    print(client.get_note_link(note_id))

### 步骤6：验证

    content = client.read_note_content(note_id)
    assert content.get("word_count", 0) > 100, f"字数不足"

## 关键配置

| 配置项 | 值 |
|--------|-----|
| 笔记标签 | `<DIARY_TAG>`（XML内嵌，不用API添加） |
| 语音音色 | `<YOUR_NOIZ_VOICE_ID>`（台湾腔） |
| 语音格式 | mp3 |
| 语速 | 0.9 |
| 图片基准图 | `<DATA_DIR>/cherry_high_fashion_v4.png` |
| 图片参考权重 | 0.85 |
| 图片比例 | 16:9（横屏，适配日记插入） |
| 穿搭生成器 | `diary_prompt_generator.py` v5.0 |
| 训练缓存 | `<DATA_DIR>/tunji_cache/{date}.json` |
| 天气缓存 | `<DATA_DIR>/weather_cache/{date}.json` |
| 聊天记忆 | `<MEMORY_DIR>/chat/YYYY-MM-DD.md` |
| 语音输出 | `<DATA_DIR>/diary_voice/diary_{date}.mp3` |

## 版本历史

| 版本 | 变更 |
|------|------|
| v5.0 | 表情库重写：中等幅度变化（15-25词/条）+ 眼神融入每条表情；嘴唇约束改为独立轻量句（`Soft natural lips`）；新增禁止否定描述规则 |
| v4.0 | 自然语言连贯 prompt；低角度仰拍全身构图；因果式大胸描述；光线方向+效果；表情库融入眼神；删除独立人体/眼神锚定 |
| v3.3 | 基础版：穿搭随机+场景随机+表情随机 |