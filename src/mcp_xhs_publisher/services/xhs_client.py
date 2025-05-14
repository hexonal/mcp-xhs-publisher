"""
小红书客户端服务

提供小红书API的客户端封装，包括登录、cookie管理等功能
"""
import os
import sys
import time
import shutil
import tempfile
import requests
from typing import List, Optional, Dict, Any, Union, Callable

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

    def __init__(self, account: str, cookie_dir: Optional[str] = None, sign_url: Optional[str] = None, 
                 use_sign: bool = True, login_method: str = "qrcode", phone: Optional[str] = None):
        """
        初始化小红书客户端。
        Args:
            account: 账号标识（如手机号、邮箱或自定义名）
            cookie_dir: cookie 存储目录，默认 ~/.xhs_cookies
            sign_url: 签名服务 URL（可选）
            use_sign: 是否使用签名服务，默认为True
            login_method: 登录方式，支持"qrcode"(二维码)和"phone"(手机验证码)，默认为"qrcode"
            phone: 当login_method为"phone"时的手机号
        """
        self.account = account
        # 确保cookie目录路径中的~被展开
        self.cookie_dir = os.path.expanduser(cookie_dir or os.path.expanduser("~/.xhs_cookies"))
        self.cookie_path = os.path.join(self.cookie_dir, f"{account}.cookie")
        self.sign_url = sign_url
        self.use_sign = use_sign
        self.client = None
        self.login_method = login_method
        self.phone = phone

        if not os.path.exists(self.cookie_dir):
            os.makedirs(self.cookie_dir)

        # 创建签名函数（仅当use_sign为True且sign_url不为空时）
        sign_function = None
        if self.use_sign and self.sign_url:
            sign_function = self._create_sign_function(self.sign_url)

        cookie = load_cookie(self.cookie_path)
        if cookie and cookie_valid(cookie, self.REQUIRED_COOKIE_KEYS):
            self.client = XhsClient(cookie=cookie, sign=sign_function)
            if not self._is_logged_in():
                print("cookie 已失效或无效，需重新登录")
                self._login()
        else:
            self._login()

    def _login(self):
        """根据登录方式选择相应的登录方法"""
        if self.login_method == "phone" and self.phone:
            self._login_by_phone(self.phone)
        else:
            self._login_by_qrcode()

    def _create_sign_function(self, sign_url: Optional[str]) -> Optional[Callable]:
        """
        创建签名函数
        
        Args:
            sign_url: 签名服务URL，如果为None或空则不使用签名服务
            
        Returns:
            签名函数或None
        """
        # 如果没有提供签名URL，返回None
        if not sign_url:
            return None
            
        def sign_function(url: str, data: dict, **kwargs) -> Dict[str, str]:
            """调用签名服务获取签名"""
            try:
                # 从cookie中提取a1和web_session
                cookie = kwargs.get("cookie", "")
                a1 = ""
                web_session = ""
                
                if cookie:
                    for item in cookie.split(";"):
                        item = item.strip()
                        if item.startswith("a1="):
                            a1 = item[3:]
                        elif item.startswith("web_session="):
                            web_session = item[12:]
                
                response = requests.post(
                    sign_url,
                    json={
                        "uri": url,
                        "data": data,
                        "a1": a1,
                        "web_session": web_session
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    signs = response.json()
                    return {
                        "x-s": signs["x-s"],
                        "x-t": signs["x-t"]
                    }
                else:
                    print(f"签名服务请求失败: {response.status_code} - {response.text}")
                    return {}
            except Exception as e:
                print(f"调用签名服务出错: {e}")
                return {}
                
        return sign_function

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
        # 使用配置加载工具获取配置
        config = load_xhs_config()
        
        # 解析命令行参数获取签名URL
        sign_url = None
        for idx, val in enumerate(sys.argv):
            if val == "--sign-url" and idx + 1 < len(sys.argv):
                sign_url = sys.argv[idx + 1]
            elif val.startswith("--sign-url="):
                sign_url = val.split("--sign-url=")[1]
        
        # 如果命令行中没有，则检查环境变量
        if not sign_url:
            sign_url = os.environ.get("XHS_SIGN_URL") or config.get("sign_url", "")
        
        # 检查是否禁用签名（用于调试或不需要签名的环境）
        use_sign = config.get("use_sign", "true").lower() != "false"
        
        # 获取登录方式和手机号
        login_method = config.get("login_method", "qrcode")
        phone = config.get("phone", "")
        
        return XhsApiClient(
            account=config["account"], 
            cookie_dir=config.get("cookie_dir"), 
            sign_url=sign_url,
            use_sign=use_sign,
            login_method=login_method,
            phone=phone
        )

    def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            info = self.client.get_self_info()
            return bool(info and info.get("nickname"))
        except Exception:
            return False

    def _login_by_qrcode(self):
        """通过二维码登录"""
        # 创建签名函数（仅当use_sign为True且sign_url不为空时）
        sign_function = None
        if self.use_sign and self.sign_url:
            sign_function = self._create_sign_function(self.sign_url)
        
        try:
            self.client = XhsClient(sign=sign_function)
            qrcode = self.client.get_qrcode()
            print(f"请扫码登录，二维码链接：{qrcode['url']}")
            
            # 检查返回的qrcode是否有效
            if not qrcode.get('url'):
                error_msg = f"获取二维码失败: {qrcode}"
                print(error_msg)
                raise Exception(error_msg)
                
            for _ in range(60):
                try:
                    status = self.client.check_qrcode(qrcode['id'], qrcode['code'])
                    if status.get("cookie") and cookie_valid(status["cookie"], self.REQUIRED_COOKIE_KEYS):
                        save_cookie(self.cookie_path, status["cookie"])
                        self.client = XhsClient(cookie=status["cookie"], sign=sign_function)
                        if self._is_logged_in():
                            print("登录成功！")
                            return
                except Exception as e:
                    print(f"检查二维码状态出错: {e}")
                time.sleep(2)
            raise Exception("二维码登录超时")
        except Exception as e:
            error_details = str(e)
            print(f"登录过程出错: {error_details}")
            
            if 'sign' in error_details.lower() or 'x-sign' in error_details.lower():
                suggestion = "可能是签名服务问题，请尝试设置 XHS_USE_SIGN=false 禁用签名"
                print(suggestion)
                error_details += f"。{suggestion}"
                
            raise Exception(f"二维码登录失败: {error_details}")

    def _login_by_phone(self, phone: str, area_code: str = "+86"):
        """
        通过手机验证码登录
        
        Args:
            phone: 手机号
            area_code: 国家/地区代码，默认+86(中国大陆)
        """
        # 创建签名函数（仅当use_sign为True且sign_url不为空时）
        sign_function = None
        if self.use_sign and self.sign_url:
            sign_function = self._create_sign_function(self.sign_url)
        
        try:
            # 初始化未登录状态的客户端
            self.client = XhsClient(sign=sign_function)
            
            # 发送验证码
            send_result = self.client.send_phone_code(phone=phone, area_code=area_code)
            if not send_result or not send_result.get("success", False):
                error_msg = send_result.get("error_msg", "未知错误") if send_result else "未知错误"
                raise Exception(f"发送验证码失败: {error_msg}")
                
            print(f"验证码已发送到手机 {phone}")
            
            # 请求用户输入验证码
            max_attempts = 3
            for attempt in range(max_attempts):
                code = input("请输入验证码: ")
                
                try:
                    # 检查验证码
                    check_result = self.client.check_code(phone, code, area_code=area_code)
                    token = check_result.get("mobile_token")
                    if not token:
                        print("验证码验证失败，未获取到token")
                        continue
                        
                    # 使用token登录
                    login_result = self.client.login_code(phone, token, area_code=area_code)
                    
                    # 检查登录结果
                    if login_result and login_result.get("cookie") and cookie_valid(login_result["cookie"], self.REQUIRED_COOKIE_KEYS):
                        # 保存cookie
                        save_cookie(self.cookie_path, login_result["cookie"])
                        
                        # 使用新cookie创建客户端
                        self.client = XhsClient(cookie=login_result["cookie"], sign=sign_function)
                        
                        if self._is_logged_in():
                            print(f"手机号 {phone} 登录成功！")
                            return
                        else:
                            raise Exception("登录成功但验证失败，请重新尝试")
                    else:
                        error_msg = login_result.get("error_msg", "未知错误") if login_result else "未知错误"
                        raise Exception(f"登录失败: {error_msg}")
                    
                except DataFetchError as e:
                    print(f"验证码验证失败: {e}")
                    if attempt < max_attempts - 1:
                        print(f"还有 {max_attempts - attempt - 1} 次尝试机会")
                    else:
                        raise Exception(f"验证码尝试次数过多，登录失败: {e}")
                        
        except Exception as e:
            error_details = str(e)
            print(f"手机验证码登录失败: {error_details}")
            
            if 'sign' in error_details.lower() or 'x-sign' in error_details.lower():
                suggestion = "可能是签名服务问题，请尝试设置 XHS_USE_SIGN=false 禁用签名"
                print(suggestion)
                error_details += f"。{suggestion}"
                
            raise Exception(f"手机验证码登录失败: {error_details}")

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
                content=content,
                image_paths=None,
                video_path=None,
                topics=topics
            )
            return {"status": "success", "type": "text", "result": result}
        except Exception as e:
            return {"status": "error", "type": "text", "error": str(e)}

    def create_image_note(self, content: str, image_paths: List[str], topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """创建图文笔记"""
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

    def create_video_note(self, content: str, video_path: str, cover_path: Optional[str] = None, topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """创建视频笔记"""
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

    def send_code(self, phone: str, area_code: str = "+86") -> Dict[str, Any]:
        """
        发送手机验证码
        
        Args:
            phone: 手机号
            area_code: 国家/地区代码，默认+86(中国大陆)
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        # 创建签名函数（仅当use_sign为True且sign_url不为空时）
        sign_function = None
        if self.use_sign and self.sign_url:
            sign_function = self._create_sign_function(self.sign_url)
        
        try:
            # 初始化未登录状态的客户端
            if not self.client:
                self.client = XhsClient(sign=sign_function)
            
            # 请求发送验证码
            result = self.client.send_phone_code(phone=phone, area_code=area_code)
            
            # 检查返回结果
            if result and result.get("success", False):
                return {"status": "success", "message": "验证码已发送"}
            else:
                error_msg = result.get("error_msg", "未知错误") if result else "未知错误"
                return {"status": "error", "message": f"发送验证码失败: {error_msg}"}
                
        except Exception as e:
            error_details = str(e)
            print(f"发送验证码失败: {error_details}")
            
            if 'sign' in error_details.lower() or 'x-sign' in error_details.lower():
                error_details += "。可能是签名服务问题，请尝试设置 XHS_USE_SIGN=false 禁用签名"
                
            return {"status": "error", "message": f"发送验证码失败: {error_details}"}
    
    def login_code(self, phone: str, code: str, area_code: str = "+86") -> Dict[str, Any]:
        """
        使用验证码登录
        
        Args:
            phone: 手机号
            code: 验证码
            area_code: 国家/地区代码，默认+86(中国大陆)
            
        Returns:
            Dict[str, Any]: 登录结果
        """
        # 创建签名函数（仅当use_sign为True且sign_url不为空时）
        sign_function = None
        if self.use_sign and self.sign_url:
            sign_function = self._create_sign_function(self.sign_url)
        
        try:
            # 初始化未登录状态的客户端
            if not self.client:
                self.client = XhsClient(sign=sign_function)
            
            # 使用验证码登录
            result = self.client.login_phone(phone=phone, code=code, area_code=area_code)
            
            # 检查返回结果
            if result and result.get("cookie") and cookie_valid(result["cookie"], self.REQUIRED_COOKIE_KEYS):
                # 保存cookie
                save_cookie(self.cookie_path, result["cookie"])
                
                # 使用新cookie创建客户端
                self.client = XhsClient(cookie=result["cookie"], sign=sign_function)
                
                if self._is_logged_in():
                    print(f"手机号 {phone} 登录成功！")
                    return {"status": "success", "message": "登录成功"}
                else:
                    raise Exception("登录成功但验证失败，请重新尝试")
            else:
                error_msg = result.get("error_msg", "未知错误") if result else "未知错误"
                raise Exception(f"登录失败: {error_msg}")
                
        except Exception as e:
            error_details = str(e)
            print(f"验证码登录失败: {error_details}")
            
            if 'sign' in error_details.lower() or 'x-sign' in error_details.lower():
                error_details += "。可能是签名服务问题，请尝试设置 XHS_USE_SIGN=false 禁用签名"
                
            raise Exception(f"验证码登录失败: {error_details}") 