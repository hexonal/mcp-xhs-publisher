import os
from typing import List

def log_info(message: str) -> None:
    """
    输出信息级别日志。
    Args:
        message: 日志内容
    """
    print(f"[INFO] {message}")

def log_error(message: str) -> None:
    """
    输出错误级别日志。
    Args:
        message: 日志内容
    """
    print(f"[ERROR] {message}")

def check_files_exist(paths: List[str]) -> bool:
    """
    检查给定的文件路径列表是否全部存在。
    Args:
        paths: 文件路径列表
    Returns:
        bool: 全部存在返回 True，否则 False
    """
    return all(os.path.isfile(p) for p in paths) 