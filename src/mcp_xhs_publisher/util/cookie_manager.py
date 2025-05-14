"""
Cookie管理工具

提供cookie的加载、保存和验证功能
"""
import os
from typing import List, Optional


def load_cookie(cookie_path: str) -> Optional[str]:
    """
    从文件加载cookie
    
    Args:
        cookie_path: cookie文件路径
        
    Returns:
        加载的cookie字符串，如果文件不存在或为空则返回None
    """
    if os.path.exists(cookie_path):
        with open(cookie_path, "r") as f:
            cookie = f.read().strip()
            return cookie if cookie else None
    return None


def save_cookie(cookie_path: str, cookie: str) -> None:
    """
    保存cookie到文件
    
    Args:
        cookie_path: cookie文件保存路径
        cookie: cookie字符串
    """
    with open(cookie_path, "w") as f:
        f.write(cookie)


def cookie_valid(cookie: str, required_keys: List[str]) -> bool:
    """
    检查cookie是否包含必要字段。
    
    Args:
        cookie: cookie字符串
        required_keys: 必须包含的key列表
        
    Returns:
        bool: 全部包含返回True，否则False
    """
    for key in required_keys:
        if key not in cookie:
            return False
    return True


def get_cookie_dir(account: str = "default") -> str:
    """
    获取cookie存储目录
    
    Args:
        account: 账号标识
        
    Returns:
        cookie存储目录路径
    """
    cookie_dir = os.path.expanduser("~/.xhs_cookies")
    if not os.path.exists(cookie_dir):
        os.makedirs(cookie_dir)
    return cookie_dir 