"""
配置加载工具

负责从环境变量和命令行参数加载小红书配置
"""
from dataclasses import dataclass
import argparse
import os
import sys
from typing import Dict

@dataclass
class XhsConfig:
    cookie_dir: str
    cookie_name: str
    log_level: str = "INFO"
    sign_url: str = ""
    use_sign: bool = True

def load_xhs_config() -> XhsConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookie-dir', type=str, required=False, help='cookie 存储目录')
    parser.add_argument('--cookie-name', type=str, required=False, help='cookie 文件名')
    parser.add_argument('--log-level', type=str, required=False, help='日志级别')
    parser.add_argument('--sign-url', type=str, required=False, help='签名服务URL')
    parser.add_argument('--use-sign', type=str, required=False, help='是否使用签名服务（true/false）')
    args, _ = parser.parse_known_args()

    cookie_dir = args.cookie_dir or os.environ.get("XHS_COOKIE_DIR")
    cookie_name = args.cookie_name or os.environ.get("XHS_COOKIE_NAME")
    log_level = args.log_level or os.environ.get("XHS_LOG_LEVEL") or "INFO"
    sign_url = args.sign_url or os.environ.get("XHS_SIGN_URL") or ""
    use_sign_str = args.use_sign or os.environ.get("XHS_USE_SIGN") or "true"
    use_sign = use_sign_str.lower() != "false"

    if not cookie_dir or not cookie_name:
        raise ValueError("必须通过 --cookie-dir/--cookie-name 或 XHS_COOKIE_DIR/XHS_COOKIE_NAME 指定 cookie 路径和文件名。")

    return XhsConfig(
        cookie_dir=os.path.expanduser(cookie_dir),
        cookie_name=cookie_name,
        log_level=log_level,
        sign_url=sign_url,
        use_sign=use_sign
    )

def get_log_level_from_config() -> str:
    """
    从配置中获取日志级别
    
    Returns:
        str: 日志级别
    """
    config = load_xhs_config()
    return config.log_level

def get_sign_url_from_config() -> str:
    """
    从配置中获取签名服务URL
    
    Returns:
        str: 签名服务URL，如果未指定则返回空字符串
    """
    config = load_xhs_config()
    return config.sign_url

def get_use_sign_from_config() -> bool:
    """
    从配置中获取是否使用签名服务
    
    Returns:
        bool: 是否使用签名服务
    """
    config = load_xhs_config()
    return config.use_sign

# 如果直接运行此模块，打印配置信息
if __name__ == "__main__":
    try:
        config = load_xhs_config()
        print("加载的小红书配置:")
        for key, value in config.__dict__.items():
            if key in ["sign_url"]:  # 敏感信息不显示完整内容
                print(f"  {key}: ***")
            else:
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"加载配置失败: {e}") 