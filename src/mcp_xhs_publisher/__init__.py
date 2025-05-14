"""
MCP XHS Publisher

小红书自动发布的 Model Context Protocol (MCP) 工具，支持文本、图文、视频笔记一键发布

此包通过MCP协议提供小红书自动发布功能，支持:
- 文本笔记发布
- 图文笔记发布
- 视频笔记发布

用法示例：
    # 启动MCP服务器
    $ python -m mcp_xhs_publisher

    # 使用指定端口启动
    $ python -m mcp_xhs_publisher --port=8081
"""

__version__ = "0.1.0"

from .config import config
from .tools.tool_registry import ToolRegistry 