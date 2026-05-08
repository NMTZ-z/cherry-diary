#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集模块：训记训练数据 + 天气数据
所有数据自动缓存到本地，避免重复请求
"""

import os
import re
import json
import requests
from datetime import datetime

# ============ 训记 APP ============

TUNJI_API_URL = "https://trains.xunjiapp.cn/api_trains_for_llm"
TUNJI_API_KEY = os.environ.get("TUNJI_API_KEY", "")
TUNJI_CACHE_DIR = os.path.join(os.environ.get("CHERRY_DATA_DIR", "./data"), "tunji_cache")

os.makedirs(TUNJI_CACHE_DIR, exist_ok=True)


def _fetch_tunji_raw(date_str):
    """请求训记API，自动缓存"""
    cache_file = os.path.join(TUNJI_CACHE_DIR, f"{date_str}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        # 只信任新格式缓存（带source字段），旧格式缓存需重新请求
        if cached.get("source") == "api_trains_for_llm":
            return cached
        else:
            print(f"[tunji] 缓存格式过期，重新请求")
    headers = {
        "Authorization": f"Bearer {TUNJI_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            TUNJI_API_URL, headers=headers, json={"datestr": date_str}, timeout=15
        )
        data = r.json()
        # 只有当返回非空时才缓存，避免缓存空结果
        cache_data = {
            "source": "api_trains_for_llm",
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        if data.get("res"):
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"[tunji] 缓存成功: {len(data['res'])} 条记录")
        else:
            print(f"[tunji] API返回空数据，不缓存")
        return data
    except Exception as e:
        print(f"[tunji] 请求失败: {e}")
        return {"res": []}


def _parse_training_record(raw_line):
    """
    解析单条训练记录文本
    格式: 260414,id:xxx,训练名称,train_time:xxx,calorie:401,1.动作名,1组,50kg,10次,time:60s,...
    """
    parts = raw_line.split(",")
    result = {
        "id": "",
        "name": "",
        "train_time": "",
        "calorie": 0,
        "exercises": [],
    }
    exercises = {}
    current_exercise_num = None
    current_set = None

    for part in parts:
        part = part.strip()

        if part.startswith("id:"):
            result["id"] = part[3:]
        elif part.startswith("train_time:"):
            result["train_time"] = part[11:]
        elif part.startswith("calorie:"):
            result["calorie"] = int(part[8:])
        elif re.match(r"^\d+\.(?!\d)", part):
            match = re.match(r"^(\d+)\.(.*)", part)
            num = int(match.group(1))
            ex_name = match.group(2)
            current_exercise_num = num
            current_set = None
            exercises[num] = {"name": ex_name, "sets": []}
        elif re.match(r"^\d+组$", part):
            current_set = int(part.replace("组", ""))
        elif re.match(r"\d+kg", part):
            weight = float(part.replace("kg", ""))
            if (
                current_set is not None
                and current_exercise_num is not None
                and current_exercise_num in exercises
            ):
                exercises[current_exercise_num]["sets"].append(
                    {"set": current_set, "weight": weight}
                )
        elif re.match(r"\d+次", part):
            reps = int(part.replace("次", ""))
            if (
                current_set is not None
                and current_exercise_num is not None
                and exercises[current_exercise_num]["sets"]
            ):
                exercises[current_exercise_num]["sets"][-1]["reps"] = reps

    # 提取训练名称：紧跟 id:xxx 之后的第一个非特殊字段
    name_found = False
    for part in parts:
        part = part.strip()
        if part.startswith(("id:", "train_time:", "calorie:", "time:")):
            name_found = False
            continue
        if re.match(r"^\d+\.(?!\d)", part):
            break
        if name_found:
            # 紧跟 id 的下一个字段就是训练名称
            result["name"] = part
            break
        if part.startswith("id:"):
            name_found = True

    # 备用方案：如果上面没找到，用 parts[2]（已知格式中名称固定在第三个位置）
    if not result["name"] and len(parts) > 2 and not parts[2].startswith(("id:", "train_time:", "calorie:")):
        result["name"] = parts[2]

    for num in sorted(exercises.keys()):
        result["exercises"].append(exercises[num])

    return result


def get_training(date_str=None):
    """
    获取并解析指定日期的训练数据
    date_str: YYYY-MM-DD，默认今天
    返回: list of parsed records，无训练返回空列表
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    data = _fetch_tunji_raw(date_str)
    # 兼容新旧缓存格式：新格式res在data字段内，旧格式res在顶层
    if "data" in data and isinstance(data["data"], dict) and "res" in data["data"]:
        raw_records = data["data"]["res"]
    else:
        raw_records = data.get("res", [])
    if not raw_records:
        return []
    return [_parse_training_record(r) for r in raw_records]


def format_training(records):
    """
    将解析后的训练数据格式化为日记展示用文本
    records: get_training() 返回值
    返回: (有训练bool, 格式化文本str)
    """
    if not records:
        return False, ""

    parts = []
    total_calories = 0

    for record in records:
        name = record.get("name", "训练")
        calories = record.get("calorie", 0)
        total_calories += calories
        if calories:
            parts.append(f"{name} · {calories}大卡")
        else:
            parts.append(name)

        for ex in record["exercises"]:
            sets = ex["sets"]
            if not sets:
                continue

            weights = sorted(set(s["weight"] for s in sets if s["weight"] > 0))
            if weights and weights[0] > 0:
                if len(weights) == 1:
                    weight_str = f"{int(weights[0]) if weights[0] == int(weights[0]) else weights[0]}kg"
                else:
                    weight_str = f"{int(weights[0]) if weights[0] == int(weights[0]) else weights[0]}→{int(weights[-1]) if weights[-1] == int(weights[-1]) else weights[-1]}kg"
                max_weight_sets = [s for s in sets if s["weight"] == weights[-1]]
                reps = max_weight_sets[0]["reps"] if max_weight_sets else sets[-1]["reps"]
                parts.append(f"{ex['name']} {weight_str}×{len(max_weight_sets)}×{reps}")
            else:
                reps = sets[0]["reps"]
                parts.append(f"{ex['name']} {len(sets)}×{reps}")

    if total_calories:
        parts.append(f"总消耗 {total_calories}大卡")

    return True, "\n".join(parts)


# ============ 天气 ============

WEATHER_CACHE_DIR = os.path.join(os.environ.get("CHERRY_DATA_DIR", "./data"), "weather_cache")
os.makedirs(WEATHER_CACHE_DIR, exist_ok=True)

def _weather_to_cn(desc_en):
    """英文天气描述转中文，支持多关键词匹配"""
    d = desc_en.lower().strip()
    if "thunder" in d:
        return "雷暴"
    if "heavy snow" in d:
        return "大雪"
    if "moderate snow" in d or "light snow" in d or "blizzard" in d:
        return "雪"
    if "heavy rain" in d:
        return "大雨"
    if "moderate rain" in d:
        return "中雨"
    if any(kw in d for kw in ["light rain", "drizzle", "patchy rain"]):
        return "小雨"
    if "fog" in d:
        return "雾"
    if "mist" in d or "haze" in d:
        return "薄雾"
    if "overcast" in d:
        return "阴"
    if "cloudy" in d:
        return "多云"
    if "partly cloudy" in d:
        return "多云转晴"
    if "sunny" in d or "clear" in d:
        return "晴"
    return desc_en


def get_weather(city=None, date_str=None):
    if city is None:
        city = os.environ.get("WEATHER_CITY", "Beijing")
    """
    获取天气数据，自动缓存（每天只请求一次）
    返回: dict {desc_cn, temp, humidity, wind}
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    cache_file = os.path.join(WEATHER_CACHE_DIR, f"{date_str}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        r = requests.get(f"https://wttr.in/{city}?format=j1&lang=zh", timeout=10)
        r.raise_for_status()
        d = r.json()
        current = d["current_condition"][0]
        # 优先用 wttr.in 的中文描述（修复 double-encoded UTF-8 问题）
        desc_cn = current.get("lang_zh", [{}])[0].get("value", "")
        if desc_cn:
            try:
                # wttr.in 的 lang_zh 经常返回 double-encoded UTF-8
                # 修复：将字符串编码为 latin-1 还原原始字节，再按 UTF-8 解码
                desc_cn = desc_cn.encode("latin-1").decode("utf-8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                # 如果 latin-1 → utf-8 失败，尝试直接作为英文翻译
                desc_en = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
                desc_cn = _weather_to_cn(desc_en)
        else:
            desc_en = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            desc_cn = _weather_to_cn(desc_en)

        result = {
            "desc_cn": desc_cn,
            "temp": int(current.get("temp_C", 0)),
            "humidity": current.get("humidity", ""),
            "wind": current.get("windspeedKmph", ""),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
    except Exception as e:
        print(f"[weather] 获取失败: {e}")
        return {"desc_cn": "未知", "temp": 0, "humidity": "", "wind": ""}


if __name__ == "__main__":
    print("=== 训记 4月14日 ===")
    records = get_training("2026-04-14")
    has_t, text = format_training(records)
    print(f"有训练: {has_t}  名称: {records[0]['name'] if records else '-'}")
    print(text)

    print(f"\n=== 无训练日 ===")
    records_none = get_training("2026-04-15")
    has_t2, text2 = format_training(records_none)
    print(f"有训练: {has_t2}")

    print(f"\n=== 天气 ===")
    w = get_weather()
    print(f"{w['desc_cn']} {w['temp']}°C")