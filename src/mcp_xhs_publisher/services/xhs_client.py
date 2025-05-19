"""
小红书客户端服务

提供小红书API的客户端封装，包括登录、cookie管理等功能
"""
import os
import shutil
import sys
import tempfile
import time
from typing import List, Optional, Dict, Any

import requests

try:
    from xhs import XhsClient, DataFetchError
except ImportError:
    XhsClient = None  # 仅便于类型提示，实际运行需安装 xhs 包
    DataFetchError = Exception

from ..util.cookie_manager import load_cookie, save_cookie, cookie_valid
from ..util.config_loader import load_xhs_config


class XhsApiClient:
    """
    小红书API客户端，封装XhsClient并提供额外功能
    """
    REQUIRED_COOKIE_KEYS = ["a1", "web_session", "webId"]

    def __init__(self, cookie_dir: str):
        """
        初始化小红书客户端。
        Args:
            cookie_dir: cookie 存储目录，必须显式指定
        """
        self.cookie_dir = os.path.expanduser(cookie_dir)
        self.client = None

        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)

        cookie = load_cookie(self.cookie_dir)
        if cookie and cookie_valid(cookie, self.REQUIRED_COOKIE_KEYS):
            self.client = XhsClient(cookie=cookie)
        else:
            raise RuntimeError("未获取到有效的小红书 cookie，请先登录或配置 cookie 后重试。")

    @staticmethod
    def build_from_env() -> "XhsApiClient":
        """
        从环境变量和命令行参数构建客户端。
        必须显式指定 cookie_dir 和 cookie_name。
        Returns:
            XhsApiClient 实例
        Raises:
            ValueError: 如果未找到必要的账号信息
        """
        config = load_xhs_config()
        return XhsApiClient(
            cookie_dir=config.cookie_dir
        )

    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            info = self.client.get_self_info()
            return bool(info and info.get("nickname"))
        except Exception:
            return False
    def _download_images(self, image_paths: List[str]) -> (List[str], List[str]):
        """
        下载 https 图片到临时目录，返回本地路径列表和临时文件列表。
        """
        local_paths = []
        tmp_files = []
        for path in image_paths:
            if path.startswith("https://") or path.startswith("http://"):
                tmp_dir = tempfile.gettempdir()
                filename = os.path.join(tmp_dir, os.path.basename(path).split("?")[0])
                try:
                    resp = requests.get(path, stream=True, timeout=10)
                    resp.raise_for_status()
                    with open(filename, "wb") as f:
                        shutil.copyfileobj(resp.raw, f)
                    local_paths.append(filename)
                    tmp_files.append(filename)
                except Exception as e:
                    print(f"图片下载失败: {path}, 错误: {e}")
            else:
                local_paths.append(path)
        return local_paths, tmp_files

    def get_self_info(self) -> Dict[str, Any]:
        """获取当前登录用户信息"""
        return self.client.get_self_info()

    def get_note_by_id(self, note_id: str) -> Dict[str, Any]:
        """获取笔记信息"""
        return self.client.get_note_by_id(note_id)

    def create_text_note(self, content: str, topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """创建纯文本笔记"""
        try:
            result = self.client.create_note(
                title="",
                desc=content,
                note_type="normal",
                topics=topics or []
            )
            return {"status": "success", "type": "text", "result": result}
        except Exception as e:
            return {"status": "error", "type": "text", "error": str(e)}

    def create_image_note(self, content: str, image_paths: List[str], topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """创建图文笔记"""
        tmp_files = []
        try:
            local_paths, tmp_files = self._download_images(image_paths)
            result = self.client.create_image_note(
                title="",
                desc=content,
                files=local_paths,
                topics=topics or []
            )
            return {"status": "success", "type": "image", "result": result}
        except Exception as e:
            return {"status": "error", "type": "image", "error": str(e)}
        finally:
            for f in tmp_files:
                try:
                    os.remove(f)
                except Exception:
                    pass

    def create_video_note(self, content: str, video_path: str, cover_path: Optional[str] = None, topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """创建视频笔记"""
        try:
            result = self.client.create_video_note(
                title="",
                desc=content,
                video_path=video_path,
                cover_path=cover_path,
                topics=topics or []
            )
            return {"status": "success", "type": "video", "result": result}
        except Exception as e:
            return {"status": "error", "type": "video", "error": str(e)} 