"""
日志工具

提供统一的日志记录功能，使用JSON格式输出
"""
import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """将日志记录格式化为JSON字符串"""
        log_data: Dict[str, Any] = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
        }
        # 尝试将 message 反序列化为 dict，避免重复转义
        msg = record.getMessage()
        try:
            msg_obj = json.loads(msg)
            if isinstance(msg_obj, dict):
                log_data.update(msg_obj)
            else:
                log_data["message"] = msg
        except Exception:
            log_data["message"] = msg
        
        # 添加异常信息（如果有）
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # 添加自定义字段（如果有）
        if hasattr(record, "data") and record.data:
            log_data.update(record.data)
            
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name: str = "mcp_xhs_publisher", level: int = None) -> logging.Logger:
    """
    设置并返回一个配置好的logger，使用JSON格式输出
    
    Args:
        name: logger名称
        level: 日志级别，如果为None则从配置中获取
        
    Returns:
        配置好的logger对象
    """
    # 如果未指定日志级别，从配置中获取
    if level is None:
        try:
            from .config_loader import get_log_level_from_config
            level = get_log_level_from_config()
        except (ImportError, ValueError):
            # 如果无法导入或无法获取配置，使用默认值
            level = logging.INFO
    
    # 禁用根日志器，防止日志输出到stdout
    logging.getLogger().handlers = []
    
    # 判断是否在MCP环境中运行
    in_mcp_mode = not sys.stdout.isatty()
    
    # 在MCP模式下输出到日志文件，而不是stderr
    if in_mcp_mode:
        # 创建日志目录
        log_dir = os.path.expanduser("~/.mcp_xhs_publisher/logs")
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception:
                # 如果无法创建目录，则回退到临时目录
                log_dir = "/tmp"
        
        # 使用日志文件
        log_file = os.path.join(log_dir, "mcp_xhs_publisher.log")
        handler = logging.FileHandler(log_file, encoding="utf-8")
    else:
        # 在终端模式下使用stderr
        handler = logging.StreamHandler(sys.stderr)
    
    # 配置根日志器
    root_formatter = JsonFormatter()
    handler.setFormatter(root_formatter)
    logging.getLogger().handlers = [handler]
    logging.getLogger().setLevel(level)
    
    # 配置模块日志器
    logger = logging.getLogger(name)
    logger.handlers = []  # 清除可能存在的旧处理器
    logger.propagate = False  # 防止日志传递到根日志器
    logger.setLevel(level)
    
    # 添加同样的处理器到模块日志器
    module_handler = handler
    formatter = JsonFormatter()
    module_handler.setFormatter(formatter)
    logger.addHandler(module_handler)
    
    return logger


def add_log_data(logger: logging.Logger, **kwargs) -> logging.Logger:
    """
    为日志记录添加自定义字段
    
    Args:
        logger: 日志器实例
        **kwargs: 要添加的键值对数据
        
    Returns:
        更新了LoggerAdapter的日志器
    """
    class CustomAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs.setdefault('extra', {}).setdefault('data', {})
            kwargs['extra']['data'].update(self.extra)
            return msg, kwargs
    
    return CustomAdapter(logger, kwargs)


def log_info(message: str, logger: Optional[logging.Logger] = None, **data) -> None:
    """
    记录信息级别日志，JSON格式
    
    Args:
        message: 日志消息
        logger: 可选的logger对象，如不提供则使用默认logger
        **data: 要添加到JSON日志中的额外数据
    """
    if logger:
        if data:
            logger = add_log_data(logger, **data)
        logger.info(message)
    else:
        # 判断是否在MCP环境中运行
        in_mcp_mode = not sys.stdout.isatty()
        
        if in_mcp_mode:
            # 在MCP模式下使用文件日志
            _log_to_file("INFO", message, data)
        else:
            # 在终端模式下输出JSON格式到stderr
            log_data = {
                "timestamp": time.time(),
                "level": "INFO",
                "message": message
            }
            if data:
                log_data.update(data)
            print(json.dumps(log_data, ensure_ascii=False), file=sys.stderr)


def log_error(message: str, logger: Optional[logging.Logger] = None, **data) -> None:
    """
    记录错误级别日志，JSON格式
    
    Args:
        message: 日志消息
        logger: 可选的logger对象，如不提供则使用默认logger
        **data: 要添加到JSON日志中的额外数据
    """
    if logger:
        if data:
            logger = add_log_data(logger, **data)
        logger.error(message)
    else:
        # 判断是否在MCP环境中运行
        in_mcp_mode = not sys.stdout.isatty()
        
        if in_mcp_mode:
            # 在MCP模式下使用文件日志
            _log_to_file("ERROR", message, data)
        else:
            # 在终端模式下输出JSON格式到stderr
            log_data = {
                "timestamp": time.time(),
                "level": "ERROR",
                "message": message
            }
            if data:
                log_data.update(data)
            print(json.dumps(log_data, ensure_ascii=False), file=sys.stderr)


def log_debug(message: str, logger: Optional[logging.Logger] = None, **data) -> None:
    """
    记录调试级别日志，JSON格式
    
    Args:
        message: 日志消息
        logger: 可选的logger对象，如不提供则使用默认logger
        **data: 要添加到JSON日志中的额外数据
    """
    if logger:
        if data:
            logger = add_log_data(logger, **data)
        logger.debug(message)
    else:
        # 判断是否在MCP环境中运行
        in_mcp_mode = not sys.stdout.isatty()
        
        if in_mcp_mode:
            # 在MCP模式下使用文件日志
            _log_to_file("DEBUG", message, data)
        else:
            # 在终端模式下输出JSON格式到stderr
            log_data = {
                "timestamp": time.time(),
                "level": "DEBUG",
                "message": message
            }
            if data:
                log_data.update(data)
            print(json.dumps(log_data, ensure_ascii=False), file=sys.stderr)


def _log_to_file(level: str, message: str, data: Dict[str, Any]) -> None:
    """
    将日志写入文件
    
    Args:
        level: 日志级别
        message: 日志消息
        data: 附加数据
    """
    log_dir = os.path.expanduser("~/.mcp_xhs_publisher/logs")
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            # 如果无法创建目录，则回退到临时目录
            log_dir = "/tmp"
    
    log_file = os.path.join(log_dir, "mcp_xhs_publisher.log")
    
    # 构造日志数据
    log_data = {
        "timestamp": time.time(),
        "level": level,
        "message": message
    }
    if data:
        log_data.update(data)
    
    # 写入日志文件
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
    except Exception:
        # 如果写入失败，无需进一步处理
        pass


# 默认logger实例
logger = setup_logger() 