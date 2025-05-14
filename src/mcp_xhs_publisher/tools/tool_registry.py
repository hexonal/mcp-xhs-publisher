"""
MCP工具注册模块

负责注册所有小红书发布相关的MCP工具和资源
"""
from typing import Any, List, Optional, Dict, TYPE_CHECKING
import traceback

# 条件导入以避免循环引用
if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..models.tool_io_schemas import (
    PublishTextInput,
    PublishImageInput,
    PublishVideoInput,
    LoginResponse  # 添加手机登录输入模型导入
)
from .publish_executor import PublishExecutor
from ..services.xhs_client import XhsApiClient
from ..util.config_loader import get_use_sign_from_config
# from .. import __main__  # 已废弃，避免循环导入
from ..ready_flag import SERVER_READY

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
        self._register_login_tools(mcp_server)
        self._register_publish_tools(mcp_server)
        self._register_resource_tools(mcp_server)
    
    def _register_login_tools(self, mcp_server: "FastMCP") -> None:
        """
        注册登录相关工具
        
        Args:
            mcp_server: MCP服务器实例
        """
        
        @mcp_server.tool(
            name="generate_qrcode",
            description="生成小红书账号登录二维码（不阻塞，需配合 check_qrcode_status 轮询）"
        )
        def generate_qrcode() -> Dict[str, Any]:
            """
            生成小红书账号登录二维码（不阻塞）
            Returns:
                Dict[str, Any]: 二维码信息，包含二维码URL、ID、Code
            """
            # 检查全局ready标志
            from .. import ready_flag
            if not getattr(ready_flag, "SERVER_READY", True):
                return {
                    "status": "error",
                    "message": "服务初始化中，请稍后重试",
                    "error": "MCP服务器尚未初始化完成，无法处理请求。"
                }
            try:
                client = XhsApiClient()
                qrcode_info = client.client.get_qrcode()
                self.executor.client = client
                return {
                    "status": "success",
                    "message": "二维码生成成功，请使用小红书APP扫描",
                    "qr_url": qrcode_info["url"],
                    "qr_id": qrcode_info["id"],
                    "qr_code": qrcode_info["code"]
                }
            except Exception as e:
                import logging
                error_msg = str(e)
                error_type = type(e).__name__
                tb = traceback.format_exc()
                suggestions = []
                if "sign" in error_msg.lower():
                    suggestions.append("尝试设置XHS_USE_SIGN=false禁用签名")
                suggestion_text = "建议: " + "; ".join(suggestions) if suggestions else ""
                # 详细日志
                logging.error(f"生成二维码失败: {error_type}: {error_msg}\nTraceback:\n{tb}")
                return {
                    "status": "error",
                    "message": "生成二维码失败",
                    "error": f"{error_type}: {error_msg}. {suggestion_text}",
                    "traceback": tb
                }

        @mcp_server.tool(
            name="check_qrcode_status",
            description="检查二维码扫描状态（单次检查，需前端/调用方轮询）"
        )
        def check_qrcode_status(qr_id: str, qr_code: str) -> Dict[str, Any]:
            """
            检查二维码扫描状态（单次检查）
            Args:
                qr_id: 二维码ID
                qr_code: 二维码Code
            Returns:
                Dict[str, Any]: 扫描状态，如果成功则包含用户信息
            """
            try:
                client = self.executor.client
                check_result = client.client.check_qrcode(qr_id, qr_code)
                code_status = check_result.get("code_status", 0)
                if code_status == 2 and check_result.get("cookie"):
                    client.client = XhsClient(cookie=check_result["cookie"], sign=client.sign)
                    setattr(client.client, "sign", client.sign)
                    from ..util.cookie_manager import save_cookie
                    save_cookie(client.cookie_path, check_result["cookie"])
                    return {
                        "status": "success",
                        "message": "登录成功"
                    }
                elif code_status in (3, 4):
                    return {
                        "status": "error",
                        "message": "登录失败或二维码已失效"
                    }
                else:
                    return {
                        "status": "pending",
                        "message": "等待扫码或确认"
                    }
            except Exception as e:
                error_msg = str(e)
                return {
                    "status": "error",
                    "message": "检查二维码状态失败",
                    "error": error_msg
                }

        @mcp_server.tool(
            name="check_login_status",
            description="检查小红书账号的登录状态，验证是否已登录且登录是否有效"
        )
        def check_login_status() -> Dict[str, Any]:
            """
            检查小红书账号的登录状态
            
            Returns:
                Dict[str, Any]: 登录状态，包含状态和用户信息（如果已登录）
            """
            try:
                # 从环境变量创建客户端实例
                client = XhsApiClient.build_from_env()
                
                # 检查登录状态
                user_info = client.get_self_info()
                
                # 将客户端设置为执行器的客户端
                self.executor.client = client
                
                return LoginResponse(
                    status="success",
                    message="已登录",
                    user_info=user_info
                ).dict()
            except Exception as e:
                # 未登录或登录失效
                error_msg = str(e)
                suggestions = []
                
                # 根据错误类型提供建议
                if "sign" in error_msg.lower():
                    suggestions.append("尝试设置XHS_USE_SIGN=false禁用签名")
                
                if not get_use_sign_from_config() and 'cookie' not in error_msg.lower():
                    suggestions.append("您已禁用签名，请确保小红书API支持无签名访问")
                
                suggestion_text = "建议: " + "; ".join(suggestions) if suggestions else ""
                
                return LoginResponse(
                    status="error",
                    message="未登录或登录已失效",
                    error=f"{error_msg}. {suggestion_text}"
                ).dict()
    
    def _register_publish_tools(self, mcp_server: "FastMCP") -> None:
        """
        注册发布相关工具
        
        Args:
            mcp_server: MCP服务器实例
        """
        
        @mcp_server.tool(
            name="publish_text",
            description="发布纯文本笔记到小红书平台，支持添加话题标签"
        )
        def publish_text(content: str, topics: Optional[List[str]] = None) -> Dict[str, Any]:
            """
            发布纯文本笔记到小红书
            
            Args:
                content: 笔记文本内容
                topics: 话题关键词列表（可选）
                
            Returns:
                Dict[str, Any]: 发布结果，包含笔记ID和发布时间等信息
            """
            params = PublishTextInput(
                content=content,
                topics=topics
            )
            result = self.executor.publish_text(params)
            return result.dict()

        @mcp_server.tool(
            name="publish_image",
            description="发布图文笔记到小红书平台，支持多张图片和话题标签"
        )
        def publish_image(content: str, image_paths: List[str], topics: Optional[List[str]] = None) -> Dict[str, Any]:
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
                content=content,
                image_paths=image_paths,
                topics=topics
            )
            result = self.executor.publish_image(params)
            return result.dict()

        @mcp_server.tool(
            name="publish_video",
            description="发布视频笔记到小红书平台，支持自定义封面和话题标签"
        )
        def publish_video(content: str, video_path: str, cover_path: Optional[str] = None, topics: Optional[List[str]] = None) -> Dict[str, Any]:
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
                topics=topics
            )
            result = self.executor.publish_video(params)
            return result.dict()
    
    def _register_resource_tools(self, mcp_server: "FastMCP") -> None:
        """
        注册资源相关工具
        
        Args:
            mcp_server: MCP服务器实例
        """
        
        @mcp_server.resource(
            "xhs-note://{note_id}",
            name="小红书笔记资源",
            description="获取小红书笔记的详细信息，包含内容、图片和作者等数据"
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
                    "note_id": note_id
                }

        @mcp_server.resource(
            "xhs-user://",
            name="小红书用户资源",
            description="获取当前登录的小红书用户的详细信息，包含昵称、头像和粉丝数等数据"
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
                return {
                    "status": "error",
                    "message": f"获取用户信息失败: {str(e)}"
                } 