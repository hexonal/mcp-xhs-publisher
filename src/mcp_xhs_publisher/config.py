"""
配置管理模块

管理MCP服务器配置，支持从环境变量、命令行参数和配置文件加载配置
符合MCP服务器指南中关于配置管理的建议
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """
    MCP服务器配置管理类
    
    提供统一的配置管理接口，支持多种配置来源：
    - 配置文件
    - 环境变量
    - 命令行参数
    
    遵循MCP服务器指南中的最佳实践，提供安全、灵活的配置管理
    """
    
    # 服务器名称 - 固定值，不可配置
    SERVER_NAME = "mcp-xhs-publisher"
    
    # 配置项敏感度标记，用于日志和错误处理
    SENSITIVE_KEYS = [
        "xhs_sign_url",
        "cookie",
        "xhs_account"  # 账号作为敏感信息
    ]
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理类
        
        Args:
            config_file: 可选的配置文件路径，如果提供则从该文件加载配置
        """
        self._config = {}
        
        # 按优先级从低到高加载配置
        if config_file:
            self._load_from_file(config_file)
        self._load_from_env()
        self._load_from_args()
        
        # 初始化时验证关键配置
        self._validate_config()
    
    def _load_from_file(self, config_file: str) -> None:
        """
        从配置文件加载配置
        
        Args:
            config_file: 配置文件路径，支持JSON格式
            
        Raises:
            ValueError: 配置文件格式无效时可能引发异常，但会被捕获并仅记录警告
        """
        path = Path(config_file)
        if not path.exists():
            logging.warning(f"配置文件不存在: {config_file}")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                if not isinstance(file_config, dict):
                    raise ValueError("配置文件必须包含JSON对象")
                self._config.update(file_config)
                logging.info(f"已从配置文件 {config_file} 加载配置")
        except json.JSONDecodeError as e:
            logging.error(f"配置文件格式错误: {e}")
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
    
    def _load_from_env(self) -> None:
        """
        从环境变量加载配置
        
        遵循MCP服务器指南建议，支持通过环境变量进行配置，适用于容器化部署
        """
        # MCP服务器配置
        env_mapping = {
            "MCP_LOG_LEVEL": "log_level",
            "XHS_COOKIE_DIR": "xhs_cookie_dir"
        }
        
        for env_name, config_key in env_mapping.items():
            if env_name in os.environ:
                value = os.environ[env_name]
                
                # 对于路径配置，展开~为用户主目录
                if env_name == "XHS_COOKIE_DIR" and "~" in value:
                    value = os.path.expanduser(value)
                
                self._config[config_key] = value
                
                # 对于敏感配置项，不在日志中显示具体值
                if any(key in config_key.lower() for key in self.SENSITIVE_KEYS):
                    logging.info(f"已从环境变量加载配置项: {config_key}=***")
                else:
                    logging.info(f"已从环境变量加载配置项: {config_key}={value}")
    
    def _load_from_args(self) -> None:
        """
        从命令行参数加载配置
        
        支持以下格式的命令行参数:
        - --key=value
        - --key value
        """
        args = sys.argv[1:]
        for i, arg in enumerate(args):
            # 参数格式: --key=value 或 --key value
            if arg.startswith("--"):
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    self._set_config_from_arg(key, value)
                elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                    key = arg[2:]
                    value = args[i + 1]
                    self._set_config_from_arg(key, value)
    
    def _set_config_from_arg(self, key: str, value: str) -> None:
        """
        根据参数名设置配置
        
        Args:
            key: 参数名
            value: 参数值
        """
        key_map = {
            "log-level": "log_level",
            "cookie-dir": "xhs_cookie_dir"
        }
        
        config_key = key_map.get(key, key)
        
        # 对于路径配置，展开~为用户主目录
        if key == "cookie-dir" and "~" in value:
            value = os.path.expanduser(value)
            
        self._config[config_key] = value
            
        # 记录日志，对敏感信息做脱敏处理
        if any(sensitive in config_key.lower() for sensitive in self.SENSITIVE_KEYS):
            logging.info(f"已从命令行参数设置配置项: {config_key}=***")
        else:
            logging.info(f"已从命令行参数设置配置项: {config_key}={value}")
    
    def _validate_config(self) -> None:
        """
        验证配置的完整性和有效性
        """
        # 确保log_level存在，如果不存在则设置为INFO
        if "log_level" not in self._config:
            self._config["log_level"] = "INFO"
            
        # 如果没有设置cookie目录，则使用默认值
        if "xhs_cookie_dir" not in self._config:
            self._config["xhs_cookie_dir"] = os.path.expanduser("~/.xhs_cookies")
        elif isinstance(self._config["xhs_cookie_dir"], str) and "~" in self._config["xhs_cookie_dir"]:
            # 确保cookie目录路径中的~被展开
            self._config["xhs_cookie_dir"] = os.path.expanduser(self._config["xhs_cookie_dir"])
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置项名称
            default: 默认值，当配置项不存在时返回
            
        Returns:
            Any: 配置项的值
        """
        # 对于server_name，总是返回固定值
        if key == "server_name":
            return self.SERVER_NAME
        return self._config.get(key, default)
    
    def get_log_level(self) -> int:
        """
        获取日志级别
        
        将字符串日志级别转换为logging模块常量
        
        Returns:
            int: 日志级别常量
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        level_str = self.get("log_level", "INFO").upper()
        return level_map.get(level_str, logging.INFO)
    
    def __getitem__(self, key: str) -> Any:
        """
        字典访问方式获取配置
        
        Args:
            key: 配置项名称
            
        Returns:
            Any: 配置项的值
            
        Raises:
            KeyError: 如果配置项不存在
        """
        if key == "server_name":
            return self.SERVER_NAME
        if key in self._config:
            return self._config[key]
        raise KeyError(f"配置项不存在: {key}")
    
    def as_dict(self) -> Dict[str, Any]:
        """
        返回所有配置项
        
        Returns:
            Dict[str, Any]: 配置字典的副本
        """
        config_dict = self._config.copy()
        config_dict["server_name"] = self.SERVER_NAME
        return config_dict
    
    def get_server_options(self) -> Dict[str, Any]:
        """
        获取MCP服务器选项
        
        Returns:
            Dict[str, Any]: 服务器配置选项字典
        """
        return {
            "name": self.SERVER_NAME
        }


# 全局配置实例
config = Config() 