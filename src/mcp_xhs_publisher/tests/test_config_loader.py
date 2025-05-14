"""
配置加载模块测试

测试环境变量和命令行参数的配置加载功能
"""
import os
import sys
import unittest
from unittest.mock import patch

from ..util.config_loader import load_xhs_config, _normalize_param_name, get_log_level_from_config


class TestConfigLoader(unittest.TestCase):
    """测试配置加载工具函数"""
    
    def setUp(self):
        """测试前的设置，清除环境变量"""
        # 保存原始环境变量和命令行参数
        self.original_env = os.environ.copy()
        self.original_argv = sys.argv.copy()
        
        # 清除相关环境变量
        for key in list(os.environ.keys()):
            if key.startswith("XHS_") or key.startswith("MCP_"):
                del os.environ[key]
    
    def tearDown(self):
        """测试后的清理，恢复环境变量"""
        # 恢复原始环境变量和命令行参数
        os.environ.clear()
        os.environ.update(self.original_env)
        sys.argv = self.original_argv
    
    def test_normalize_param_name(self):
        """测试参数名称标准化"""
        self.assertEqual(_normalize_param_name("--account"), "account")
        self.assertEqual(_normalize_param_name("--cookie-dir"), "cookie_dir")
        self.assertEqual(_normalize_param_name("--sign_url"), "sign_url")
        self.assertEqual(_normalize_param_name("-a"), "a")
        self.assertEqual(_normalize_param_name("XHS_ACCOUNT"), "XHS_ACCOUNT")  # 不会处理非前缀部分
    
    def test_load_from_env(self):
        """测试从环境变量加载配置"""
        # 设置环境变量
        os.environ["XHS_ACCOUNT"] = "test_account"
        os.environ["XHS_COOKIE_DIR"] = "~/test_cookies"
        os.environ["XHS_SIGN_URL"] = "http://test.sign.url"
        
        # 加载配置
        config = load_xhs_config()
        
        # 验证结果
        self.assertEqual(config["account"], "test_account")
        self.assertEqual(config["cookie_dir"], os.path.expanduser("~/test_cookies"))
        self.assertEqual(config["sign_url"], "http://test.sign.url")
    
    def test_load_from_argv(self):
        """测试从命令行参数加载配置"""
        # 设置命令行参数
        sys.argv = ["script.py", "--account", "cli_account", 
                   "--cookie-dir", "~/cli_cookies", 
                   "--sign_url", "http://cli.sign.url"]
        
        # 加载配置
        config = load_xhs_config()
        
        # 验证结果
        self.assertEqual(config["account"], "cli_account")
        self.assertEqual(config["cookie_dir"], os.path.expanduser("~/cli_cookies"))
        self.assertEqual(config["sign_url"], "http://cli.sign.url")
    
    def test_alternative_argv_format(self):
        """测试替代格式的命令行参数"""
        # 设置命令行参数
        sys.argv = ["script.py", "--account=alt_account", 
                   "--cookie-dir=~/alt_cookies", 
                   "--sign_url=http://alt.sign.url"]
        
        # 加载配置
        config = load_xhs_config()
        
        # 验证结果
        self.assertEqual(config["account"], "alt_account")
        self.assertEqual(config["cookie_dir"], os.path.expanduser("~/alt_cookies"))
        self.assertEqual(config["sign_url"], "http://alt.sign.url")
    
    def test_cli_overrides_env(self):
        """测试命令行参数覆盖环境变量"""
        # 设置环境变量
        os.environ["XHS_ACCOUNT"] = "env_account"
        os.environ["XHS_COOKIE_DIR"] = "~/env_cookies"
        os.environ["XHS_SIGN_URL"] = "http://env.sign.url"
        
        # 设置命令行参数
        sys.argv = ["script.py", "--account", "override_account"]
        
        # 加载配置
        config = load_xhs_config()
        
        # 验证结果 - 命令行参数应覆盖环境变量
        self.assertEqual(config["account"], "override_account")
        self.assertEqual(config["cookie_dir"], os.path.expanduser("~/env_cookies"))
        self.assertEqual(config["sign_url"], "http://env.sign.url")
    
    def test_param_aliases(self):
        """测试参数别名支持"""
        # 设置基本账号，因为它是必需的
        os.environ["XHS_ACCOUNT"] = "base_account"
        
        # 测试 xhs-account 别名
        sys.argv = ["script.py", "--xhs-account", "alias1"]
        config = load_xhs_config()
        self.assertEqual(config["account"], "alias1")
        
        # 测试 xhs_account 别名
        sys.argv = ["script.py", "--xhs_account", "alias2"]
        config = load_xhs_config()
        self.assertEqual(config["account"], "alias2")
        
        # 测试 cookies 别名
        sys.argv = ["script.py", "--cookies", "~/cookies_dir"]
        config = load_xhs_config()
        self.assertEqual(config["cookie_dir"], os.path.expanduser("~/cookies_dir"))
        
        # 测试 cookie_path 别名
        sys.argv = ["script.py", "--cookie_path", "~/other_path"]
        config = load_xhs_config()
        self.assertEqual(config["cookie_dir"], os.path.expanduser("~/other_path"))
        
        # 测试 signurl 别名
        sys.argv = ["script.py", "--signurl", "http://sign.url"]
        config = load_xhs_config()
        self.assertEqual(config["sign_url"], "http://sign.url")
        
        # 测试 sign-url 别名
        sys.argv = ["script.py", "--sign-url", "http://other.sign.url"]
        config = load_xhs_config()
        self.assertEqual(config["sign_url"], "http://other.sign.url")
    
    def test_missing_account(self):
        """测试缺少账号信息时抛出异常"""
        # 不设置账号信息
        with self.assertRaises(ValueError) as context:
            load_xhs_config()
        
        self.assertIn("未提供小红书账号", str(context.exception))
    
    def test_log_level_config(self):
        """测试日志级别配置"""
        # 从环境变量获取
        os.environ["XHS_ACCOUNT"] = "log_test"
        os.environ["MCP_LOG_LEVEL"] = "debug"
        
        config = load_xhs_config()
        self.assertEqual(config["log_level"], "debug")
        
        # 从命令行参数获取（优先级更高）
        sys.argv = ["script.py", "--account", "log_test", "--log-level", "ERROR"]
        config = load_xhs_config()
        self.assertEqual(config["log_level"], "ERROR")
        
        # 测试log-level别名
        sys.argv = ["script.py", "--account", "log_test", "--loglevel", "WARNING"]
        config = load_xhs_config()
        self.assertEqual(config["log_level"], "WARNING")
        
        # 测试日志级别转换函数
        os.environ["XHS_ACCOUNT"] = "log_test"
        os.environ["MCP_LOG_LEVEL"] = "DEBUG"
        
        import logging
        self.assertEqual(get_log_level_from_config(), logging.DEBUG)
        
        # 测试非法日志级别
        os.environ["MCP_LOG_LEVEL"] = "INVALID_LEVEL"
        self.assertEqual(get_log_level_from_config(), logging.INFO)  # 默认是INFO
    
    def test_boolean_flag(self):
        """测试布尔标志参数"""
        # 设置命令行参数，包含无值的标志
        sys.argv = ["script.py", "--account", "flag_test", "--debug"]
        
        # 这个测试主要验证解析布尔标志不会导致错误
        # 实际上我们目前没有使用这样的标志，但代码应该能正确处理
        config = load_xhs_config()
        self.assertEqual(config["account"], "flag_test")


if __name__ == "__main__":
    unittest.main() 