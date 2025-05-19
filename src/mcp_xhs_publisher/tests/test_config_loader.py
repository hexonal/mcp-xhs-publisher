"""
配置加载模块测试

测试环境变量和命令行参数的配置加载功能
"""
import os
import sys
import unittest

from mcp_xhs_publisher.util.config_loader import load_xhs_config, get_log_level_from_config


class TestConfigLoader(unittest.TestCase):
    """测试配置加载工具函数"""
    
    def setUp(self):
        """测试前的设置，清除相关环境变量"""
        self.original_env = os.environ.copy()
        self.original_argv = sys.argv.copy()
        for key in list(os.environ.keys()):
            if key in ["XHS_COOKIE_DIR", "XHS_COOKIE_NAME", "XHS_LOG_LEVEL", "XHS_SIGN_URL", "XHS_USE_SIGN"]:
                del os.environ[key]
    
    def tearDown(self):
        """测试后的清理，恢复环境变量"""
        os.environ.clear()
        os.environ.update(self.original_env)
        sys.argv = self.original_argv
    
    def test_load_from_env(self):
        """测试从环境变量加载配置"""
        os.environ["XHS_COOKIE_DIR"] = "~/test_cookies"
        os.environ["XHS_COOKIE_NAME"] = "test.cookie"
        os.environ["XHS_SIGN_URL"] = "http://test.sign.url"
        os.environ["XHS_LOG_LEVEL"] = "DEBUG"
        os.environ["XHS_USE_SIGN"] = "false"
        
        config = load_xhs_config()
        
        self.assertEqual(config.cookie_dir, os.path.expanduser("~/test_cookies"))
        self.assertEqual(config.cookie_name, "test.cookie")
        self.assertEqual(config.sign_url, "http://test.sign.url")
        self.assertEqual(config.log_level, "DEBUG")
        self.assertFalse(config.use_sign)
    
    def test_load_from_argv(self):
        """测试从命令行参数加载配置"""
        sys.argv = ["script.py", "--cookie-dir", "~/cli_cookies", "--cookie-name", "cli.cookie", "--sign-url", "http://cli.sign.url", "--log-level", "ERROR", "--use-sign", "true"]
        
        config = load_xhs_config()
        
        self.assertEqual(config.cookie_dir, os.path.expanduser("~/cli_cookies"))
        self.assertEqual(config.cookie_name, "cli.cookie")
        self.assertEqual(config.sign_url, "http://cli.sign.url")
        self.assertEqual(config.log_level, "ERROR")
        self.assertTrue(config.use_sign)
    
    def test_cli_overrides_env(self):
        """测试命令行参数覆盖环境变量"""
        os.environ["XHS_COOKIE_DIR"] = "~/env_cookies"
        os.environ["XHS_COOKIE_NAME"] = "env.cookie"
        os.environ["XHS_SIGN_URL"] = "http://env.sign.url"
        os.environ["XHS_LOG_LEVEL"] = "INFO"
        os.environ["XHS_USE_SIGN"] = "false"
        
        sys.argv = ["script.py", "--cookie-dir", "~/cli_cookies", "--cookie-name", "cli.cookie", "--sign-url", "http://cli.sign.url", "--log-level", "ERROR", "--use-sign", "true"]
        
        config = load_xhs_config()
        
        self.assertEqual(config.cookie_dir, os.path.expanduser("~/cli_cookies"))
        self.assertEqual(config.cookie_name, "cli.cookie")
        self.assertEqual(config.sign_url, "http://cli.sign.url")
        self.assertEqual(config.log_level, "ERROR")
        self.assertTrue(config.use_sign)
    
    def test_missing_cookie_config(self):
        """测试缺少 cookie 配置时抛出异常"""
        # 不设置 cookie_dir 和 cookie_name
        with self.assertRaises(ValueError) as context:
            load_xhs_config()
        
        self.assertIn("cookie 路径和文件名", str(context.exception))
    
    def test_log_level_config(self):
        """测试日志级别配置"""
        os.environ["XHS_COOKIE_DIR"] = "~/log_cookies"
        os.environ["XHS_COOKIE_NAME"] = "log.cookie"
        os.environ["XHS_LOG_LEVEL"] = "debug"
        
        config = load_xhs_config()
        self.assertEqual(config.log_level, "debug")
        
        # 从命令行参数获取（优先级更高）
        sys.argv = ["script.py", "--cookie-dir", "~/log_cookies", "--cookie-name", "log.cookie", "--log-level", "ERROR"]
        config = load_xhs_config()
        self.assertEqual(config.log_level, "ERROR")
    
    def test_use_sign_flag(self):
        """测试 use_sign 标志参数"""
        os.environ["XHS_COOKIE_DIR"] = "~/flag_cookies"
        os.environ["XHS_COOKIE_NAME"] = "flag.cookie"
        os.environ["XHS_USE_SIGN"] = "false"
        
        config = load_xhs_config()
        self.assertFalse(config.use_sign)
        
        sys.argv = ["script.py", "--cookie-dir", "~/flag_cookies", "--cookie-name", "flag.cookie", "--use-sign", "true"]
        config = load_xhs_config()
        self.assertTrue(config.use_sign)


if __name__ == "__main__":
    unittest.main() 