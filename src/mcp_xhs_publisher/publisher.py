import os
import sys
import time
import shutil
import tempfile
import requests
from typing import List, Optional, Dict

try:
    from xhs import XhsClient
except ImportError:
    XhsClient = None  # 仅便于类型提示，实际运行需安装 xhs 包

REQUIRED_COOKIE_KEYS = ["a1", "web_session", "webId"]

class Publisher:
    """
    小红书笔记发布器，支持文本、图文、视频三种模式。
    支持扫码登录与 cookie 持久化，自动检测登录状态。
    """
    def __init__(self, account: str, cookie_dir: Optional[str] = None, sign_url: Optional[str] = None):
        """
        初始化发布器。
        Args:
            account: 账号标识（如手机号、邮箱或自定义名）
            cookie_dir: cookie 存储目录，默认 ~/.xhs_cookies
            sign_url: 签名服务 URL（可选）
        """
        self.account = account
        self.cookie_dir = cookie_dir or os.path.expanduser("~/.xhs_cookies")
        self.cookie_path = os.path.join(self.cookie_dir, f"{account}.cookie")
        self.sign_url = sign_url
        self.client = None

        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)

        cookie = self._load_cookie()
        if cookie and self._cookie_valid(cookie):
            self.client = XhsClient(cookie=cookie, sign_url=sign_url)
            if not self._is_logged_in():
                print("cookie 已失效或无效，需重新扫码登录")
                self._login_by_qrcode()
        else:
            self._login_by_qrcode()

    @staticmethod
    def build() -> "Publisher":
        """
        构建 Publisher 实例，支持从命令行参数和环境变量读取配置。
        优先级：命令行参数 > 环境变量 > 默认值
        Returns:
            Publisher 实例
        """
        account = os.getenv("XHS_ACCOUNT", "default")
        cookie_dir = os.getenv("XHS_COOKIE_DIR", os.path.expanduser("~/.xhs_cookies"))
        sign_url = os.getenv("XHS_SIGN_URL", "")
        for idx, val in enumerate(sys.argv):
            if val == "--account" and idx + 1 < len(sys.argv):
                account = sys.argv[idx + 1]
            elif val == "--cookie-dir" and idx + 1 < len(sys.argv):
                cookie_dir = sys.argv[idx + 1]
            elif val == "--sign_url" and idx + 1 < len(sys.argv):
                sign_url = sys.argv[idx + 1]
            elif val.startswith("--account="):
                account = val.split("--account=")[1]
            elif val.startswith("--cookie-dir="):
                cookie_dir = val.split("--cookie-dir=")[1]
            elif val.startswith("--sign_url="):
                sign_url = val.split("--sign_url=")[1]
        return Publisher(account=account, cookie_dir=cookie_dir, sign_url=sign_url)

    def _load_cookie(self) -> Optional[str]:
        if os.path.exists(self.cookie_path):
            with open(self.cookie_path, "r") as f:
                cookie = f.read().strip()
                return cookie if cookie else None
        return None

    def _save_cookie(self, cookie: str):
        with open(self.cookie_path, "w") as f:
            f.write(cookie)

    def _cookie_valid(self, cookie: str) -> bool:
        """
        检查 cookie 是否包含必要字段。
        """
        for key in REQUIRED_COOKIE_KEYS:
            if key not in cookie:
                return False
        return True

    def _is_logged_in(self) -> bool:
        try:
            info = self.client.get_self_info()
            return bool(info and info.get("nickname"))
        except Exception:
            return False

    def _login_by_qrcode(self):
        self.client = XhsClient(sign_url=self.sign_url)
        qrcode = self.client.get_qrcode()
        print(f"请扫码登录，二维码链接：{qrcode['url']}")
        for _ in range(60):
            status = self.client.check_qrcode(qrcode['id'], qrcode['code'])
            if status.get("cookie") and self._cookie_valid(status["cookie"]):
                self._save_cookie(status["cookie"])
                self.client = XhsClient(cookie=status["cookie"], sign_url=self.sign_url)
                if self._is_logged_in():
                    print("登录成功！")
                    return
            time.sleep(2)
        raise Exception("二维码登录超时")

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

    def publish_text(self, content: str, topics: Optional[List[str]] = None) -> Dict:
        """
        发布纯文本笔记
        Args:
            content: 笔记文本内容
            topics: 话题关键词列表（可选）
        Returns:
            dict: 发布结果
        """
        try:
            result = self.client.create_note(
                content=content,
                image_paths=None,
                video_path=None,
                topics=topics
            )
            return {"status": "success", "type": "text", "result": result}
        except Exception as e:
            return {"status": "error", "type": "text", "error": str(e)}

    def publish_image(self, content: str, image_paths: List[str], topics: Optional[List[str]] = None) -> Dict:
        """
        发布图文笔记
        Args:
            content: 笔记文本内容
            image_paths: 图片本地路径列表或 https 链接
            topics: 话题关键词列表（可选）
        Returns:
            dict: 发布结果
        """
        tmp_files = []
        try:
            local_paths, tmp_files = self._download_images(image_paths)
            result = self.client.create_note(
                content=content,
                image_paths=local_paths,
                video_path=None,
                topics=topics
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

    def publish_video(self, content: str, video_path: str, cover_path: Optional[str] = None, topics: Optional[List[str]] = None) -> Dict:
        """
        发布视频笔记
        Args:
            content: 笔记文本内容
            video_path: 视频本地路径
            cover_path: 封面图片路径（可选）
            topics: 话题关键词列表（可选）
        Returns:
            dict: 发布结果
        """
        try:
            result = self.client.create_note(
                content=content,
                image_paths=None,
                video_path=video_path,
                cover_path=cover_path,
                topics=topics
            )
            return {"status": "success", "type": "video", "result": result}
        except Exception as e:
            return {"status": "error", "type": "video", "error": str(e)}

def init_publisher(account: str = None, cookie_dir: str = None, sign_url: str = None) -> Publisher:
    """
    初始化发布器（便于外部直接调用）。参数可选，若为空则自动从环境变量和命令行参数读取。
    Args:
        account: 账号标识
        cookie_dir: cookie 存储目录
        sign_url: 签名服务 URL
    Returns:
        Publisher 实例
    """
    if account is not None:
        return Publisher(account, cookie_dir, sign_url)
    return Publisher.build() 