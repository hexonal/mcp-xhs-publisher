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

    def __init__(self, cookie_dir: Optional[str] = None, sign_url: Optional[str] = None, use_sign: bool = True):
        """
        初始化小红书客户端。
        Args:
            cookie_dir: cookie 存储目录，默认 ~/.xhs_cookies
            sign_url: 签名服务 URL（可选）
            use_sign: 是否使用签名服务，默认为True
        """
        self.cookie_dir = os.path.expanduser(cookie_dir or os.path.expanduser("~/.xhs_cookies"))
        self.cookie_path = os.path.join(self.cookie_dir, "default.cookie")
        self.sign_url = sign_url
        self.use_sign = True  # 强制全局 use_sign 为 True
        self.client = None

        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)

        sign_function = None
        if self.use_sign and self.sign_url:
            sign_function = self._sign

        cookie = load_cookie(self.cookie_path)
        if cookie and cookie_valid(cookie, self.REQUIRED_COOKIE_KEYS):
            self.client = XhsClient(cookie=cookie, sign=sign_function)
        else:
            self.client = XhsClient(sign=sign_function)

        if hasattr(self.client, "sign"):
            self.client.sign = self._sign

    def _sign(self, uri, data=None, a1="", web_session="", **kwargs):
        """
        签名服务调用，兼容 login_phone.py 示例，使用 self.sign_url
        """
        # 优先从 cookie 中提取 a1 和 web_session
        cookie = kwargs.get("cookie", "")
        if cookie:
            for item in cookie.split(";"):
                item = item.strip()
                if item.startswith("a1="):
                    a1 = item[3:]
                elif item.startswith("web_session="):
                    web_session = item[12:]
        try:
            res = requests.post(self.sign_url,
                               json={"uri": uri, "data": data, "a1": a1, "web_session": web_session},
                               timeout=10)
            signs = res.json()
            return {
                "x-s": signs["x-s"],
                "x-t": signs["x-t"]
            }
        except Exception as e:
            print(f"签名服务调用失败: {e}")
            return {}

    @staticmethod
    def build_from_env() -> "XhsApiClient":
        """
        从环境变量和命令行参数构建客户端。
        优先级：命令行参数 > 环境变量
        Returns:
            XhsApiClient 实例
        Raises:
            ValueError: 如果未找到必要的账号信息
        """
        config = load_xhs_config()
        sign_url = None
        for idx, val in enumerate(sys.argv):
            if val == "--sign-url" and idx + 1 < len(sys.argv):
                sign_url = sys.argv[idx + 1]
            elif val.startswith("--sign-url="):
                sign_url = val.split("--sign-url=")[1]
        if not sign_url:
            sign_url = os.environ.get("XHS_SIGN_URL") or config.get("sign_url", "")
        # 强制 use_sign 为 True
        use_sign = True
        return XhsApiClient(
            cookie_dir=config.get("cookie_dir"),
            sign_url=sign_url,
            use_sign=use_sign
        )

    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            info = self.client.get_self_info()
            return bool(info and info.get("nickname"))
        except Exception:
            return False

    def _login_by_qrcode(self):
        """通过二维码登录（仅生成二维码，不阻塞轮询）"""
        # 创建签名函数（仅当use_sign为True且sign_url不为空时）
        sign_function = None
        if self.use_sign and self.sign_url:
            sign_function = self._sign
        try:
            self.client = XhsClient(sign=sign_function)
            qrcode = self.client.get_qrcode()
            print(f"请扫码登录，二维码链接：{qrcode['url']}")
            # 检查返回的qrcode是否有效
            if not qrcode.get('url'):
                error_msg = f"获取二维码失败: {qrcode}"
                print(error_msg)
                raise Exception(error_msg)
            # 只生成二维码并返回，不做轮询和阻塞
            return qrcode
        except Exception as e:
            error_details = str(e)
            print(f"登录过程出错: {error_details}")
            if 'sign' in error_details.lower() or 'x-sign' in error_details.lower():
                suggestion = "可能是签名服务问题，请尝试设置 XHS_USE_SIGN=false 禁用签名"
                print(suggestion)
                error_details += f"。{suggestion}"
            raise Exception(f"二维码登录失败: {error_details}")

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

    @property
    def sign(self):
        """公开的签名方法访问接口"""
        return self._sign 