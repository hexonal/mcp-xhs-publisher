"""
MCP工具注册模块

负责注册所有小红书发布相关的MCP工具和资源
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

# 条件导入以避免循环引用
if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..models.tool_io_schemas import (
    PublishImageInput,
    PublishTextInput,
    PublishVideoInput,  # 添加手机登录输入模型导入
)
from .publish_executor import PublishExecutor

# from .. import __main__  # 已废弃，避免循环导入

# 导入XhsClient类，用于二维码登录
try:
    from xhs import XhsClient
except ImportError:
    XhsClient = None  # 仅便于类型提示，实际运行需安装 xhs 包


class ToolRegistry:
    """
    MCP工具注册器

    负责向MCP服务器注册所有小红书发布相关工具和资源，
    管理工具执行器的创建和生命周期
    """

    def __init__(self):
        """初始化工具注册器，创建执行器实例"""
        self.executor = PublishExecutor()

    def register_tools(self, mcp_server: "FastMCP") -> None:
        """
        向MCP服务器注册所有工具和资源

        Args:
            mcp_server: MCP服务器实例
        """
        self._register_publish_tools(mcp_server)
        self._register_resource_tools(mcp_server)

    def _register_publish_tools(self, mcp_server: "FastMCP") -> None:
        """
        注册发布相关工具

        Args:
            mcp_server: MCP服务器实例
        """

        @mcp_server.tool(
            name="publish_text",
            description="发布纯文本笔记到小红书平台，支持添加话题标签",
        )
        def publish_text(
            content: str, topics: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            发布纯文本笔记到小红书

            Args:
                content: 笔记文本内容
                topics: 话题关键词列表（可选）

            Returns:
                Dict[str, Any]: 发布结果，包含笔记ID和发布时间等信息
            """
            params = PublishTextInput(content=content, topics=topics)
            result = self.executor.publish_text(params)
            return result.dict()

        @mcp_server.tool(
            name="publish_image",
            description="发布图文笔记到小红书平台，支持多张图片和话题标签",
        )
        def publish_image(
            content: str, image_paths: List[str], topics: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            发布图文笔记到小红书

            Args:
                content: 笔记文本内容
                image_paths: 图片路径列表，支持本地路径和https链接
                topics: 话题关键词列表（可选）

            Returns:
                Dict[str, Any]: 发布结果，包含笔记ID和发布时间等信息
            """
            params = PublishImageInput(
                content=content, image_paths=image_paths, topics=topics
            )
            result = self.executor.publish_image(params)
            return result.dict()

        @mcp_server.tool(
            name="publish_video",
            description="发布视频笔记到小红书平台，支持自定义封面和话题标签",
        )
        def publish_video(
            content: str,
            video_path: str,
            cover_path: Optional[str] = None,
            topics: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """
            发布视频笔记到小红书

            Args:
                content: 笔记文本内容
                video_path: 视频文件路径
                cover_path: 封面图片路径（可选）
                topics: 话题关键词列表（可选）

            Returns:
                Dict[str, Any]: 发布结果，包含笔记ID和发布时间等信息
            """
            params = PublishVideoInput(
                content=content,
                video_path=video_path,
                cover_path=cover_path,
                topics=topics,
            )
            result = self.executor.publish_video(params)
            return result.dict()

        @mcp_server.tool(
            name="is_logged_in", description="检查当前小红书账号是否已登录，返回布尔值"
        )
        def is_logged_in() -> Dict[str, Any]:
            """
            检查当前小红书账号是否已登录
            Returns:
                Dict[str, Any]: {"logged_in": True/False}
            """
            try:
                status = self.executor.client._is_logged_in()
                return {"logged_in": status}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def _register_resource_tools(self, mcp_server: "FastMCP") -> None:
        """
        注册资源相关工具

        Args:
            mcp_server: MCP服务器实例
        """

        @mcp_server.resource(
            "xhs-note://{note_id}",
            name="小红书笔记资源",
            description="获取小红书笔记的详细信息，包含内容、图片和作者等数据",
        )
        def get_note(note_id: str) -> Dict[str, Any]:
            """
            获取小红书笔记元数据（只读资源）

            Args:
                note_id: 笔记ID

            Returns:
                Dict[str, Any]: 笔记详细信息，包含内容、图片和作者等数据
            """
            try:
                # 使用执行器的客户端实例
                client = self.executor.client
                note_data = client.get_note_by_id(note_id)
                return note_data
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"获取笔记信息失败: {str(e)}",
                    "note_id": note_id,
                }

        @mcp_server.resource(
            "xhs-user://",
            name="小红书用户资源",
            description="获取当前登录的小红书用户的详细信息，包含昵称、头像和粉丝数等数据",
        )
        def get_user_info() -> Dict[str, Any]:
            """
            获取当前用户信息（只读资源）

            Returns:
                Dict[str, Any]: 用户详细信息，包含昵称、头像和粉丝数等数据
            """
            try:
                # 使用执行器的客户端实例
                client = self.executor.client
                user_info = client.get_self_info()
                return user_info
            except Exception as e:
                return {"status": "error", "message": f"获取用户信息失败: {str(e)}"}
