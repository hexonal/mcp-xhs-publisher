"""
配置加载工具

负责从环境变量和命令行参数加载小红书配置
"""

import argparse
import os
from dataclasses import dataclass


@dataclass
class XhsConfig:
    cookie_dir: str
    log_level: str = "INFO"


def load_xhs_config() -> XhsConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cookie-dir", type=str, required=False, help="cookie 存储目录"
    )
    parser.add_argument("--log-level", type=str, required=False, help="日志级别")
    args, _ = parser.parse_known_args()

    cookie_dir = args.cookie_dir or os.environ.get("XHS_COOKIE_DIR")
    log_level = args.log_level or os.environ.get("XHS_LOG_LEVEL") or "INFO"

    if not cookie_dir:
        raise ValueError("必须通过 --cookie-dir 或 XHS_COOKIE_DIR 指定 cookie 路径。")

    return XhsConfig(cookie_dir=os.path.expanduser(cookie_dir), log_level=log_level)


def get_log_level_from_config() -> str:
    """
    从配置中获取日志级别

    Returns:
        str: 日志级别
    """
    config = load_xhs_config()
    return config.log_level


# 如果直接运行此模块，打印配置信息
if __name__ == "__main__":
    try:
        config = load_xhs_config()
        print("加载的小红书配置:")
        for key, value in config.__dict__.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"加载配置失败: {e}")
