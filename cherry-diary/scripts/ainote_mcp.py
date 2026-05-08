import os
"""
WPS笔记 MCP 客户端 v2
用于创建和编辑WPS笔记（日记写入专用）
"""

import json
import requests
import uuid
import time
import re
from typing import Dict, Any, Optional, List


class AinoteMCPClient:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.base_url = "https://ainote.kdocs.cn/mcp-svc/mcp"
        self.api_key = os.environ.get("AINOTE_API_KEY", "")
        self._headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

    def _gen_id(self):
        return str(uuid.uuid4())

    def _get_text(self, result):
        """从MCP返回值提取文本"""
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "")
        try:
            return text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text
        return ""

    def _get_structured(self, result):
        """从MCP返回值提取structuredContent"""
        structured = result.get("structuredContent")
        if isinstance(structured, str):
            try:
                return json.loads(structured)
            except:
                pass
        return structured or {}

    def _call(self, method: str, args: dict) -> dict:
        """发送MCP工具调用"""
        if not self.session_id:
            raise RuntimeError("MCP未初始化")

        payload = {
            "jsonrpc": "2.0",
            "id": self._gen_id(),
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": args,
            }
        }
        headers = {**self._headers, "mcp-session-id": self.session_id}
        resp = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        print(f"HTTP {resp.status_code} data: {resp.text[:200]}")
        resp.raise_for_status()
        # SSE格式响应：找 data: 开头的行
        for line in resp.text.split("\n"):
            if line.startswith("data: "):
                raw = line[6:]
                try:
                    raw = raw.encode("latin-1").decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
                data = json.loads(raw)
                if "error" in data:
                    raise RuntimeError(f"MCP错误: {data['error']}")
                return data.get("result", {})
        raise RuntimeError(f"无法解析MCP响应: {resp.text[:200]}")

    def initialize(self):
        """初始化MCP连接"""
        headers = self._headers
        payload = {
            "jsonrpc": "2.0",
            "id": self._gen_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "cherry-diary-v2", "version": "1.0"},
            }
        }
        resp = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        # initialize 可能返回 SSE
        for line in resp.text.split("\n"):
            if line.startswith("data: "):
                break
        self.session_id = resp.headers.get("mcp-session-id", self.session_id)
        # 通知初始化完成
        notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        requests.post(self.base_url, json=notify, headers=self._headers, timeout=10)
        print("[MCP] 初始化成功")

    def create_note(self, title: str) -> str:
        """创建笔记，返回note_id"""
        result = self._call("create_note", {"title": title})
        data = self._get_text(result)
        if data:
            parsed = json.loads(data)
            return parsed.get("note_id")
        return ""

    def get_note_outline(self, note_id: str) -> list:
        """获取笔记大纲"""
        result = self._call("get_note_outline", {"note_id": note_id})
        data = self._get_text(result)
        if data:
            parsed = json.loads(data)
            return parsed.get("blocks", []) if parsed.get("blocks") else parsed.get("items", [])
        return []

    def get_first_block_id(self, note_id: str) -> str:
        """获取笔记第一个block的ID"""
        blocks = self.get_note_outline(note_id)
        if blocks:
            return blocks[0].get("block_id") or blocks[0].get("id")
        return ""

    def edit_block(self, note_id: str, block_id: str, op: str, content: str) -> dict:
        """编辑block内容（replace/insert_after/insert_before）"""
        result = self._call("edit_block", {
            "note_id": note_id,
            "block_id": block_id,
            "op": op,
            "content": content,
        })
        if result.get("isError"):
            raise RuntimeError(f"编辑失败: {self._get_text(result)}")
        return self._get_structured(result) or {}

    def replace_first_block(self, note_id: str, content: str):
        """替换第一个block的内容。注意：替换后后续旧block仍保留，如需完全重建请删旧笔记另建新的"""
        block_id = self.get_first_block_id(note_id)
        if not block_id:
            raise RuntimeError("无法获取笔记block_id")
        return self.edit_block(note_id, block_id, "replace", content)

    def insert_image(self, note_id: str, anchor_id: str, position: str, src: str) -> Optional[str]:
        """插入图片到笔记"""
        result = self._call("insert_image", {
            "note_id": note_id,
            "anchor_id": anchor_id,
            "op": position,
            "src": src,
        })
        if result.get("isError"):
            print(f"插入图片失败: {self._get_text(result)}")
            return None
        structured = self._get_structured(result) or {}
        return structured.get("block_id")

    def insert_image_at_first(self, note_id: str, image_url: str) -> Optional[str]:
        """在笔记第一个block之后插入图片"""
        block_id = self.get_first_block_id(note_id)
        if not block_id:
            raise RuntimeError("无法获取笔记block_id")
        return self.insert_image(note_id, block_id, "after", image_url)

    def add_note_tags(self, note_id: str, tag_names: str):
        """添加标签。
        注意：传路径格式（如"日记/每日日记"）可以正确匹配父子标签，
        但路径中的每段都会作为独立标签添加，产生多余的同名标签。
        策略：先用路径格式添加确保匹配子标签，再delete_tag清理多余的同名标签。
        """
        # 添加标签（路径格式）
        result = self._call("add_note_tags", {"note_id": note_id, "tag_names": [tag_names]})
        if result.get("isError"):
            print(f"添加标签失败: {self._get_text(result)}")
            return

        # 获取笔记信息，找到多余的同名顶层标签并清理
        info_result = self._call("get_note_info", {"note_id": note_id})
        if info_result.get("isError"):
            return
        info_text = self._get_text(info_result)
        if not info_text:
            return
        info = json.loads(info_text)
        tags = info.get("tags", [])

        # 找出没有parent_id的同名标签（多余的顶层标签）
        for tag in tags:
            if tag.get("name") == tag_names and not tag.get("parent_id"):
                self._call("delete_tag", {"note_id": note_id, "tag_id": tag["tag_id"]})
                print(f"[MCP] 已清理多余标签: {tag['tag_id']}")

    def read_note_content(self, note_id: str) -> dict:
        """读取笔记完整内容"""
        result = self._call("read_note_content", {"note_id": note_id})
        data = self._get_text(result)
        if data:
            return json.loads(data)
        return {}

    def get_note_link(self, note_id: str) -> str:
        """生成笔记链接"""
        return f"https://www.kdocs.cn/l/{note_id}"
