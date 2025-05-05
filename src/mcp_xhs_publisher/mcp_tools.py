"""
MCP 工具注册模块
----------------
本文件用于注册所有小红书发布相关的 MCP 工具和资源，供 LLM Host（如 Claude、Zed）通过 MCP 协议自动发现和调用。

- 所有操作型功能通过 @mcp.tool() 装饰器注册。
- 所有只读型数据通过 @mcp.resource() 装饰器注册。
- 依赖 mcp.server.fastmcp.FastMCP（MCP Python SDK 官方推荐方式）。
- 业务逻辑由 publisher.py 提供。
- 需配合 pyproject.toml/requirements.txt 安装依赖。

依赖安装示例：
    pip install mcp xhs requests pydantic

"""
from .publisher import Publisher
from typing import List, Optional
import requests

def register_tools(mcp):
    @mcp.tool()
    def publish_text(content: str, topics: Optional[List[str]] = None, account: str = "default"):
        """
        发布纯文本笔记
        Args:
            content: 笔记文本内容
            topics: 话题关键词列表（可选）
            account: 账号标识
        Returns:
            dict: 发布结果
        """
        pub = Publisher.build()
        return pub.publish_text(content, topics)

    @mcp.tool()
    def publish_image(content: str, image_paths: List[str], topics: Optional[List[str]] = None, account: str = "default"):
        """
        发布图文笔记
        Args:
            content: 笔记文本内容
            image_paths: 图片路径列表
            topics: 话题关键词列表（可选）
            account: 账号标识
        Returns:
            dict: 发布结果
        """
        pub = Publisher.build()
        return pub.publish_image(content, image_paths, topics)

    @mcp.tool()
    def publish_video(content: str, video_path: str, cover_path: Optional[str] = None, topics: Optional[List[str]] = None, account: str = "default"):
        """
        发布视频笔记
        Args:
            content: 笔记文本内容
            video_path: 视频路径
            cover_path: 封面图片路径（可选）
            topics: 话题关键词列表（可选）
            account: 账号标识
        Returns:
            dict: 发布结果
        """
        pub = Publisher.build()
        return pub.publish_video(content, video_path, cover_path, topics)

    @mcp.resource("xhs-note://{note_id}")
    def get_note(note_id: str, account: str = "default") -> dict:
        """
        获取笔记元数据（只读资源）。
        """
        pub = Publisher.build()
        # 假设 XhsClient 有 get_note_by_id 方法
        return pub.client.get_note_by_id(note_id)

    @mcp.resource("xhs-image://{note_id}")
    def get_note_image(note_id: str, account: str = "default") -> bytes:
        """
        获取笔记首图内容（只读资源，返回图片二进制）。
        """
        pub = Publisher.build()
        note = pub.client.get_note_by_id(note_id)
        image_url = note.get("images", [None])[0]
        if not image_url:
            return b""
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        return resp.content

    @mcp.resource("xhs-user://{account}")
    def get_user_info(account: str = "default") -> dict:
        """
        获取当前用户信息（只读资源）。
        """
        pub = Publisher.build()
        return pub.client.get_self_info() 