"""
MCP XHS Publisher 主入口模块

提供命令行入口点，启动MCP服务器
"""
import sys
import logging
import os
from typing import Any, Dict

# 导入官方FastMCP SDK实现
from mcp.server.fastmcp import FastMCP

from .config import config
from .tools.tool_registry import ToolRegistry
from .util.logging import setup_logger, log_info, log_error


def create_mcp_server() -> FastMCP:
    """
    创建并配置MCP服务器
    
    Returns:
        FastMPC: 配置好的MCP服务器实例
    """
    # 设置日志 - 使用JSON格式并确保输出到stderr或日志文件
    logger = setup_logger(level=config.get_log_level())
    
    # 检查是否从环境变量加载了账号信息
    if config.get("xhs_account"):
        logger.info(f"已加载小红书账号配置，账号: ***")
    
    # 获取服务器配置
    server_name = config.get("server_name")
    
    # 创建FastMCP服务器实例，添加明确的服务器描述
    server_description = (
        "小红书自动发布MCP服务器，提供将内容发布到小红书平台的能力。"
        "支持发布纯文本、图文和视频笔记，以及查询笔记和用户信息。"
        "所有操作都需要提供小红书账号标识(account参数)，且在使用发布功能前必须先通过手机验证码登录(login_phone和verify_code)。"
        "此服务器允许大模型直接与小红书平台交互，自动创建和发布内容。"
    )
    
    mcp_server = FastMCP(
        name=server_name,
        instructions=server_description
    )
    
    # 注册工具和资源
    registry = ToolRegistry()
    registry.register_tools(mcp_server)  # ToolRegistry同时负责注册工具和资源
    
    # 记录服务器创建成功的日志（不会干扰MCP通信）
    logger.info(f"MCP服务器创建成功: {server_name}")
    
    return mcp_server


def start_server() -> None:
    """启动MCP服务器"""
    try:
        # 创建服务器
        mcp_server = create_mcp_server()
        
        # 固定使用stdio模式
        transport_mode = "sse"
        
        # 只在命令行交互模式下输出日志到终端
        in_mcp_mode = not sys.stdout.isatty()
        if not in_mcp_mode:
            # 在终端模式下，输出结构化信息
            log_info("MCP XHS Publisher 服务器启动成功", 
                     transport=transport_mode,
                     tools=[
                         "login_phone: 发送手机验证码 (必需，提供phone参数)",
                         "verify_code: 验证手机验证码完成登录 (必需，提供phone和code参数)",
                         "check_login_status: 检查登录状态 (必须提供account参数)",
                         "publish_text: 发布纯文本笔记 (必须提供account参数)",
                         "publish_image: 发布图文笔记 (必须提供account参数)",
                         "publish_video: 发布视频笔记 (必须提供account参数)"
                     ],
                     resources=[
                         "xhs-note://{account}/{note_id}: 笔记资源",
                         "xhs-user://{account}: 用户资源"
                     ],
                     config_requirement="必须通过环境变量XHS_ACCOUNT或命令行参数--account指定小红书账号")
        else:
            # 在MCP模式下，只记录到日志文件，不输出到标准输出或标准错误
            log_info("MCP XHS Publisher 服务器启动", transport=transport_mode)
        
        # 运行MCP服务器 - 使用stdio传输模式
        # 使用stdio模式，适合命令行交互或作为其他程序的子进程
        mcp_server.run(transport=transport_mode)
        
    except ImportError:
        # 日志会输出到文件而不是stderr，避免干扰MCP通信
        log_error("MCP服务器实现未找到", 
                  error="ImportError",
                  suggestion="请安装mcp[cli]或使用: pip install 'mcp-xhs-publisher[mcp]'")
        sys.exit(1)
    except KeyboardInterrupt:
        if not sys.stdout.isatty():
            log_info("服务器收到终止信号，正在关闭")
    except Exception as e:
        log_error("服务器运行出错", 
                  error=str(e),
                  error_type=type(e).__name__)
        raise


def main() -> None:
    """
    主入口函数
    
    从命令行启动MCP服务器，处理命令行参数并配置服务器
    """
    try:
        # 使用FastMCP，不需要asyncio.run
        start_server()
    except KeyboardInterrupt:
        # 记录日志但不输出到stderr
        log_info("服务器已停止", reason="KeyboardInterrupt")
    except Exception as e:
        # 记录日志但不输出到stderr
        log_error("服务器启动失败", 
                  error=str(e),
                  error_type=type(e).__name__)
        sys.exit(1)


if __name__ == "__main__":
    main()