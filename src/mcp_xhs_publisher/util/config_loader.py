"""
配置加载工具

负责从环境变量和命令行参数加载小红书配置
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 规范化参数名
def _normalize_param_name(name: str) -> str:
    """
    规范化参数名，将横线转换为下划线
    
    Args:
        name: 参数名
        
    Returns:
        规范化后的参数名
    """
    return name.replace("-", "_").lower()

# 展开路径中的~符号
def _expand_path(path: str) -> str:
    """
    展开路径中的~符号为用户主目录
    
    Args:
        path: 包含~的路径
        
    Returns:
        展开后的绝对路径
    """
    return os.path.expanduser(path) if "~" in path else path


def _get_env_variables() -> Dict[str, str]:
    """
    从环境变量中获取所有XHS_前缀和MCP_前缀的配置
    
    Returns:
        Dict[str, str]: 配置字典
    """
    env_config = {}
    
    # 查找所有XHS_前缀的环境变量
    for key, value in os.environ.items():
        if key.startswith("XHS_"):
            # 去除前缀并转换为小写
            config_key = _normalize_param_name(key[4:].lower())
            env_config[config_key] = value
        elif key.startswith("MCP_"):
            # 处理MCP前缀的环境变量
            config_key = _normalize_param_name(key[4:].lower())
            env_config[config_key] = value
            
    return env_config


def _get_argv_config() -> Dict[str, str]:
    """
    从命令行参数获取配置
    
    支持的格式:
    --key=value
    --key value
    
    Returns:
        Dict[str, str]: 配置字典
    """
    argv_config = {}
    args = sys.argv[1:]
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        # 跳过非选项参数
        if not arg.startswith("--"):
            i += 1
            continue
            
        # 处理 --key=value 格式
        if "=" in arg:
            key, value = arg[2:].split("=", 1)
            argv_config[_normalize_param_name(key)] = value
        
        # 处理 --key value 格式
        elif i + 1 < len(args) and not args[i + 1].startswith("--"):
            key = arg[2:]
            value = args[i + 1]
            argv_config[_normalize_param_name(key)] = value
            i += 1  # 额外前进一步
            
        i += 1
        
    return argv_config


def load_xhs_config() -> Dict[str, str]:
    """
    从环境变量和命令行参数加载小红书配置
    优先级：命令行参数 > 环境变量
    
    Returns:
        Dict[str, str]: 包含配置的字典
        
    Raises:
        ValueError: 如果缺少必要的配置项
    """
    config = {}
    
    # 从环境变量加载配置
    config["account"] = os.environ.get("XHS_ACCOUNT", "")
    config["cookie_dir"] = os.environ.get("XHS_COOKIE_DIR", "")
    config["sign_url"] = os.environ.get("XHS_SIGN_URL", "")
    config["use_sign"] = os.environ.get("XHS_USE_SIGN", "true")
    
    # 解析命令行参数覆盖配置
    for idx, val in enumerate(sys.argv):
        if val == "--xhs-account" and idx + 1 < len(sys.argv):
            config["account"] = sys.argv[idx + 1]
        elif val == "--xhs-cookie-dir" and idx + 1 < len(sys.argv):
            config["cookie_dir"] = sys.argv[idx + 1]
        elif val == "--sign-url" and idx + 1 < len(sys.argv):
            config["sign_url"] = sys.argv[idx + 1]
        elif val == "--xhs-use-sign" and idx + 1 < len(sys.argv):
            config["use_sign"] = sys.argv[idx + 1]
        elif val.startswith("--xhs-account="):
            config["account"] = val.split("--xhs-account=")[1]
        elif val.startswith("--xhs-cookie-dir="):
            config["cookie_dir"] = val.split("--xhs-cookie-dir=")[1]
        elif val.startswith("--sign-url="):
            config["sign_url"] = val.split("--sign-url=")[1]
        elif val.startswith("--xhs-use-sign="):
            config["use_sign"] = val.split("--xhs-use-sign=")[1]
    
    # 验证必要的配置项
    if not config["account"]:
        raise ValueError("缺少小红书账号配置。请设置环境变量 XHS_ACCOUNT 或提供命令行参数 --xhs-account")
    
    return config


def get_account_from_config() -> str:
    """
    从配置中获取账号
    
    Returns:
        str: 账号
    """
    config = load_xhs_config()
    return config["account"]


def get_log_level_from_config() -> str:
    """
    从配置中获取日志级别
    
    Returns:
        str: 日志级别
    """
    config = load_xhs_config()
    return config.get("log_level", "INFO")


def get_sign_url_from_config() -> str:
    """
    从配置中获取签名服务URL
    
    Returns:
        str: 签名服务URL，如果未指定则返回空字符串
    """
    config = load_xhs_config()
    return config.get("sign_url", "")


def get_use_sign_from_config() -> bool:
    """
    从配置中获取是否使用签名服务
    
    Returns:
        bool: 是否使用签名服务
    """
    config = load_xhs_config()
    return config.get("use_sign", "true").lower() != "false"


# 如果直接运行此模块，打印配置信息
if __name__ == "__main__":
    try:
        config = load_xhs_config()
        print("加载的小红书配置:")
        for key, value in config.items():
            if key in ["sign_url"]:  # 敏感信息不显示完整内容
                print(f"  {key}: ***")
            else:
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"加载配置失败: {e}") 