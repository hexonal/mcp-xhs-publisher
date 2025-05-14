"""
MCP XHS Publisher 主入口模块

提供命令行入口点，启动MCP服务器
"""
import sys

# 导入官方FastMCP SDK实现
from mcp.server.fastmcp import FastMCP

from .config import config
from .tools.tool_registry import ToolRegistry
from .util.logging import setup_logger, log_info, log_error
from .ready_flag import SERVER_READY as _SERVER_READY
import mcp_xhs_publisher.ready_flag as ready_flag

# 全局ready标志
SERVER_READY = False

def create_mcp_server() -> FastMCP:
    """
    创建并配置MCP服务器
    
    Returns:
        FastMPC: 配置好的MCP服务器实例
    """
    try:
        # 设置日志 - 使用JSON格式并确保输出到stderr或日志文件
        logger = setup_logger(level=config.get_log_level())
        server_name = config.get("server_name")
        server_description = (
            "小红书自动发布MCP服务器，提供将内容发布到小红书平台的能力。"
            "支持发布纯文本、图文和视频笔记，以及查询笔记和用户信息。"
            "所有操作均无需账号参数，扫码登录后自动管理cookie。"
            "此服务器允许大模型直接与小红书平台交互，自动创建和发布内容。"
        )
        mcp_server = FastMCP(
            name=server_name,
            instructions=server_description
        )
        registry = ToolRegistry()
        registry.register_tools(mcp_server)
        logger.info(f"MCP服务器创建成功: {server_name}")
        ready_flag.SERVER_READY = True
        logger.info("MCP服务器初始化完成，已准备好接收请求")
        return mcp_server
    except Exception as e:
        import traceback
        logger = setup_logger(level=config.get_log_level())
        logger.error(f"MCP服务器初始化失败: {e}\n{traceback.format_exc()}")
        print("MCP服务器初始化失败:", e)
        print(traceback.format_exc())
        raise


def start_server() -> None:
    """启动MCP服务器"""
    try:
        # 创建服务器
        mcp_server = create_mcp_server()

        # 固定使用stdio模式
        # transport_mode = "sse"  # 原先用变量，类型检查不通过

        # 只在命令行交互模式下输出日志到终端
        in_mcp_mode = not sys.stdout.isatty()
        if not in_mcp_mode:
            # 在终端模式下，输出结构化信息
            log_info("MCP XHS Publisher 服务器启动成功", 
                     transport="sse",
                     tools=[
                         "login_phone: 发送手机验证码 (必需，提供phone参数)",
                         "verify_code: 验证手机验证码完成登录 (必需，提供phone和code参数)",
                         "check_login_status: 检查登录状态",
                         "publish_text: 发布纯文本笔记",
                         "publish_image: 发布图文笔记",
                         "publish_video: 发布视频笔记"
                     ],
                     resources=[
                         "xhs-note://{note_id}: 笔记资源",
                         "xhs-user: 用户资源"
                     ],
                     config_requirement="无需账号参数，扫码登录后自动管理cookie")
        else:
            # 在MCP模式下，只记录到日志文件，不输出到标准输出或标准错误
            log_info("MCP XHS Publisher 服务器启动", transport="sse")

        # 运行MCP服务器 - 使用stdio传输模式
        # 使用字面量字符串，满足类型检查
        mcp_server.run(transport="sse")

    except ImportError:
        # 日志会输出到文件而不是stderr，避免干扰MCP通信
        log_error("MCP服务器实现未找到", 
                  error="ImportError",
                  suggestion="请安装mcp[cli]或使用: pip install 'mcp-xhs-publisher[mcXp]'")
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