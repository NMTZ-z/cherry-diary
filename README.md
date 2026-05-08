# cherry-diary

> Automated daily diary generator for AI agents. Collects weather, training data, and chat history to create illustrated voice diaries with outfit generation.

## Overview

A self-contained skill for the [WPS Lingxi Claw](https://ai.wps.cn) AI agent platform. Install by copying the `cherry-diary/` directory into your Claw skills folder.

## Installation

Copy the entire `cherry-diary/` folder to your WPS Lingxi Claw skills directory:

```
<USER_HOME>/AppData/Roaming/WPS 灵犀/serverdir/skills/cherry-diary/
```

## Dependencies

This skill requires the following skills to be installed:

- **noiz-tts**
- **ainote-mcp**

## Environment Variables

All sensitive configuration is managed via environment variables. Copy `.env.example` (if provided) to `.env` and fill in your values:

- `NOIZ_API_KEY`
- `NOIZ_VOICE_ID`
- `AINOTE_API_KEY`
- `TUNJI_API_KEY`
- `CITY_DISPLAY`
- `WEATHER_CITY`
- `CHERRY_DATA_DIR`
- `MEMORY_DIR`
- `WPS_SKILLS_DIR`

## Usage

Trigger this skill by mentioning its capabilities in your conversation with the AI agent. See `SKILL.md` for detailed usage instructions and workflow documentation.

## File Structure

```
cherry-diary/
├── SKILL.md           # Skill documentation and usage guide
└── scripts/           # Python scripts
├── scripts/ainote_mcp.py
├── scripts/diary_prompt_generator.py
├── scripts/fetch_data.py
├── scripts/main.py
└── scripts/tunji_api_reference.md

## License

[MIT License](LICENSE)
