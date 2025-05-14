import pytest
import unittest.mock as mock
from mcp_xhs_publisher.services.xhs_client import XhsApiClient
from mcp_xhs_publisher.tools.tool_registry import ToolRegistry
from mcp_xhs_publisher.models.tool_io_schemas import LoginResponse


class MockFastMCP:
    """模拟FastMCP服务器类以便测试工具注册"""
    
    def __init__(self):
        self.registered_tools = {}
    
    def tool(self, name, description):
        def decorator(func):
            self.registered_tools[name] = {
                "function": func,
                "description": description
            }
            return func
        return decorator


class TestLoginTools:
    """
    测试登录相关的工具函数
    
    这个测试类主要测试小红书手机号登录相关的功能：
    1. login_phone - 发送验证码到手机
    2. verify_code - 使用验证码完成登录
    
    对于每个工具，测试以下场景：
    - 正常情况 - 功能正确执行
    - 错误情况 - API返回错误
    - 异常情况 - 发生异常
    - 特殊参数 - 使用非默认参数
    
    测试通过模拟(mock)XhsApiClient及其方法，避免实际调用小红书API，
    使测试可以在没有网络连接或API访问权限的情况下运行。
    """
    
    @pytest.fixture
    def mcp_server(self):
        """创建模拟的MCP服务器"""
        return MockFastMCP()
    
    @pytest.fixture
    def tool_registry(self):
        """创建工具注册器"""
        return ToolRegistry()
    
    @pytest.fixture
    def registered_tools(self, mcp_server, tool_registry):
        """注册工具并返回"""
        tool_registry._register_login_tools(mcp_server)
        return mcp_server.registered_tools
    
    def test_login_phone_success(self, registered_tools):
        """测试手机号登录发送验证码成功情况"""
        # 获取login_phone工具函数
        login_phone_tool = registered_tools.get('login_phone', {}).get('function')
        assert login_phone_tool is not None, "login_phone工具未注册"
        
        # 模拟XhsApiClient类和send_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置send_code方法的返回值
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.send_code.return_value = {
                "status": "success", 
                "message": "验证码已发送"
            }
            
            # 调用login_phone工具
            result = login_phone_tool(phone="13800138000")
            
            # 验证是否调用了send_code方法
            mock_client_instance.send_code.assert_called_once_with(
                phone="13800138000", 
                area_code="+86"
            )
            
            # 验证返回值
            assert result["status"] == "pending"
            assert "验证码已发送" in result["message"]
            assert result["data"]["phone"] == "13800138000"
            assert result["data"]["area_code"] == "+86"
    
    def test_login_phone_failure(self, registered_tools):
        """测试手机号登录发送验证码失败情况"""
        # 获取login_phone工具函数
        login_phone_tool = registered_tools.get('login_phone', {}).get('function')
        assert login_phone_tool is not None, "login_phone工具未注册"
        
        # 模拟XhsApiClient类和send_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置send_code方法的返回值为失败状态
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.send_code.return_value = {
                "status": "error", 
                "message": "发送验证码失败: 请求被拒绝"
            }
            
            # 调用login_phone工具
            result = login_phone_tool(phone="13800138000")
            
            # 验证是否调用了send_code方法
            mock_client_instance.send_code.assert_called_once_with(
                phone="13800138000", 
                area_code="+86"
            )
            
            # 验证返回值
            assert result["status"] == "pending"  # 即使API返回失败，工具也应该返回pending状态
            assert "验证码已发送" in result["message"]
            assert result["data"]["phone"] == "13800138000"
    
    def test_login_phone_exception(self, registered_tools):
        """测试手机号登录发送验证码时发生异常的情况"""
        # 获取login_phone工具函数
        login_phone_tool = registered_tools.get('login_phone', {}).get('function')
        assert login_phone_tool is not None, "login_phone工具未注册"
        
        # 模拟XhsApiClient类和send_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置send_code方法抛出异常
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.send_code.side_effect = Exception("签名服务不可用")
            
            # 模拟get_use_sign_from_config函数返回False
            with mock.patch('mcp_xhs_publisher.tools.tool_registry.get_use_sign_from_config', return_value=False):
                # 调用login_phone工具
                result = login_phone_tool(phone="13800138000")
                
                # 验证是否调用了send_code方法
                mock_client_instance.send_code.assert_called_once_with(
                    phone="13800138000", 
                    area_code="+86"
                )
                
                # 验证返回值
                assert result["status"] == "error"
                assert "发送验证码失败" in result["message"]
                assert "签名服务不可用" in result["error"]
                assert "您已禁用签名" in result["error"]
    
    def test_login_phone_with_area_code(self, registered_tools):
        """测试带有区号的手机号登录"""
        # 获取login_phone工具函数
        login_phone_tool = registered_tools.get('login_phone', {}).get('function')
        assert login_phone_tool is not None, "login_phone工具未注册"
        
        # 模拟XhsApiClient类和send_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置send_code方法的返回值
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.send_code.return_value = {
                "status": "success", 
                "message": "验证码已发送"
            }
            
            # 调用login_phone工具，设置非默认区号
            result = login_phone_tool(phone="9876543210", area_code="+1")
            
            # 验证是否调用了send_code方法，并传递了正确的区号
            mock_client_instance.send_code.assert_called_once_with(
                phone="9876543210", 
                area_code="+1"
            )
            
            # 验证返回值
            assert result["status"] == "pending"
            assert "验证码已发送" in result["message"]
            assert result["data"]["area_code"] == "+1"
    
    def test_verify_code_success(self, registered_tools):
        """测试验证码验证成功情况"""
        # 获取verify_code工具函数
        verify_code_tool = registered_tools.get('verify_code', {}).get('function')
        assert verify_code_tool is not None, "verify_code工具未注册"
        
        # 模拟XhsApiClient类和login_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置login_code方法的返回值
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.login_code.return_value = {"status": "success", "message": "登录成功"}
            
            # 模拟用户信息
            mock_client_instance.get_self_info.return_value = {
                "user_id": "12345",
                "nickname": "测试用户",
                "avatar": "https://example.com/avatar.jpg"
            }
            
            # 调用verify_code工具
            result = verify_code_tool(phone="13800138000", code="123456")
            
            # 验证是否调用了login_code方法
            mock_client_instance.login_code.assert_called_once_with(
                phone="13800138000", 
                code="123456",
                area_code="+86"
            )
            
            # 验证是否调用了get_self_info方法
            mock_client_instance.get_self_info.assert_called_once()
            
            # 验证返回值
            assert result["status"] == "success"
            assert "登录成功" in result["message"]
            assert result["user_info"]["nickname"] == "测试用户"
            
            # 验证客户端是否被保存到executor中(这里只是检查是否有这行代码，实际测试中无法验证)
            # 实际代码中的 self.executor._clients[client.account] = client
    
    def test_verify_code_failure(self, registered_tools):
        """测试验证码验证失败情况"""
        # 获取verify_code工具函数
        verify_code_tool = registered_tools.get('verify_code', {}).get('function')
        assert verify_code_tool is not None, "verify_code工具未注册"
        
        # 模拟XhsApiClient类和login_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置login_code方法抛出异常
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.login_code.side_effect = Exception("验证码错误或已过期")
            
            # 模拟get_use_sign_from_config函数返回True
            with mock.patch('mcp_xhs_publisher.tools.tool_registry.get_use_sign_from_config', return_value=True):
                # 调用verify_code工具
                result = verify_code_tool(phone="13800138000", code="123456")
                
                # 验证是否调用了login_code方法
                mock_client_instance.login_code.assert_called_once_with(
                    phone="13800138000", 
                    code="123456",
                    area_code="+86"
                )
                
                # 验证返回值
                assert result["status"] == "error"
                assert "验证码验证失败" in result["message"]
                assert "验证码错误或已过期" in result["error"]
                assert "验证码可能已过期或输入错误" in result["error"]
    
    def test_verify_code_sign_error(self, registered_tools):
        """测试验证码验证时遇到签名错误的情况"""
        # 获取verify_code工具函数
        verify_code_tool = registered_tools.get('verify_code', {}).get('function')
        assert verify_code_tool is not None, "verify_code工具未注册"
        
        # 模拟XhsApiClient类和login_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置login_code方法抛出签名相关异常
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.login_code.side_effect = Exception("sign error: 签名验证失败")
            
            # 模拟get_use_sign_from_config函数返回True
            with mock.patch('mcp_xhs_publisher.tools.tool_registry.get_use_sign_from_config', return_value=True):
                # 调用verify_code工具
                result = verify_code_tool(phone="13800138000", code="123456")
                
                # 验证是否调用了login_code方法
                mock_client_instance.login_code.assert_called_once_with(
                    phone="13800138000", 
                    code="123456",
                    area_code="+86"
                )
                
                # 验证返回值
                assert result["status"] == "error"
                assert "验证码验证失败" in result["message"]
                assert "sign error" in result["error"]
                assert "尝试设置XHS_USE_SIGN=false禁用签名" in result["error"]
    
    def test_verify_code_with_area_code(self, registered_tools):
        """测试带有区号的验证码验证"""
        # 获取verify_code工具函数
        verify_code_tool = registered_tools.get('verify_code', {}).get('function')
        assert verify_code_tool is not None, "verify_code工具未注册"
        
        # 模拟XhsApiClient类和login_code方法
        with mock.patch('mcp_xhs_publisher.tools.tool_registry.XhsApiClient') as mock_client_class:
            # 设置login_code方法的返回值
            mock_client_instance = mock_client_class.return_value
            mock_client_instance.login_code.return_value = {"status": "success", "message": "登录成功"}
            
            # 模拟用户信息
            mock_client_instance.get_self_info.return_value = {
                "user_id": "12345",
                "nickname": "International User",
                "avatar": "https://example.com/avatar.jpg"
            }
            
            # 调用verify_code工具，设置非默认区号
            result = verify_code_tool(phone="9876543210", code="123456", area_code="+1")
            
            # 验证是否调用了login_code方法，并传递了正确的区号
            mock_client_instance.login_code.assert_called_once_with(
                phone="9876543210", 
                code="123456",
                area_code="+1"
            )
            
            # 验证返回值
            assert result["status"] == "success"
            assert "登录成功" in result["message"]
            assert result["user_info"]["nickname"] == "International User" 