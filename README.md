# mcp-xhs-publisher

![构建状态](https://github.com/user/mcp-xhs-publisher/workflows/构建包/badge.svg)
![代码质量](https://github.com/user/mcp-xhs-publisher/workflows/代码质量检查/badge.svg)
![Python版本](https://img.shields.io/badge/python-3.11%2B-blue)
![许可证](https://img.shields.io/github/license/user/mcp-xhs-publisher)

小红书自动发布的 Model Context Protocol (MCP) 服务器，支持文本、图文、视频笔记一键发布。

## 特性

- 🔐 支持扫码登录与多账号 cookie 管理
- 📝 支持纯文本、图文、视频笔记自动发布
- 🏷️ 支持添加话题标签
- 🔄 支持 URL 图片自动下载与处理
- 🧩 完全对齐 MCP 服务器规范，符合标准 MCP 架构
- 🤖 便于 Claude、Zed 等 LLM 应用集成调用
- 🧰 模块化设计，便于扩展新功能

## 安装

### 环境要求

- Python 3.11 及以上
- 操作系统：Windows、macOS、Linux

### 通过 pip 安装

```bash
# 安装基础包
pip install mcp-xhs-publisher

# 或包含官方MCP SDK安装（推荐）
pip install "mcp-xhs-publisher[mcp]"

# 或安装开发版本（包含代码质量工具）
pip install "mcp-xhs-publisher[dev]" 
```

### 从源码安装

```bash
git clone https://github.com/user/mcp-xhs-publisher.git
cd mcp-xhs-publisher
pip install -e .  # 或 pip install -e ".[mcp,dev]" 安装可选依赖
```

## 启动 MCP 服务器

### 命令行启动

```bash
# 使用默认配置启动
python -m mcp_xhs_publisher

# 或使用可执行脚本方式
mcp-xhs-publisher

# 指定日志级别启动
python -m mcp_xhs_publisher --log-level=DEBUG

# 指定账号
python -m mcp_xhs_publisher --account=13812345678
```

### 环境变量配置

支持通过环境变量配置：

```bash
# 设置环境变量
export MCP_LOG_LEVEL=INFO              # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
export XHS_ACCOUNT=13812345678         # 小红书账号手机号（不要有空格或其他字符）
export XHS_COOKIE_DIR=~/.xhs_cookies   # Cookie存储目录
export XHS_SIGN_URL=https://example.com/sign  # 签名服务URL

# 启动服务器
python -m mcp_xhs_publisher
```

## 命令行参数

也可以通过命令行参数进行配置：

```bash
# 使用命令行参数
python -m mcp_xhs_publisher --log-level=DEBUG --account=13812345678
```

支持的命令行参数：

- `--log-level`: 日志级别
- `--account`: 小红书账号手机号
- `--cookie-dir`: Cookie存储目录
- `--sign-url`: 签名服务URL

## 配置加载机制

项目使用了统一的配置加载机制，从环境变量和命令行参数获取配置，遵循以下优先级：

1. 命令行参数（优先级最高）
2. 环境变量（次优先级）

配置加载逻辑封装在 `config_loader` 模块中，提供了以下功能：

```python
from mcp_xhs_publisher.util.config_loader import load_xhs_config

# 加载完整配置
config = load_xhs_config()
account = config["account"]
cookie_dir = config.get("cookie_dir")
sign_url = config.get("sign_url")

# 或使用辅助函数获取特定配置
from mcp_xhs_publisher.util.config_loader import get_account_from_config, get_log_level_from_config
account = get_account_from_config()
log_level = get_log_level_from_config()  # 返回 logging.INFO 等数值
```

配置系统支持灵活的参数名称，兼容多种表述方式：

| 配置项 | 环境变量 | 命令行参数 (均可使用) |
|-------|----------|----------------------|
| 账号 | XHS_ACCOUNT | --account, --xhs-account, --xhs_account |
| Cookie目录 | XHS_COOKIE_DIR | --cookie-dir, --cookie_dir, --cookies, --cookie_path |
| 签名服务URL | XHS_SIGN_URL | --sign-url, --sign_url, --signurl |
| 日志级别 | MCP_LOG_LEVEL | --log-level, --log_level, --loglevel |

**例如**，以下配置方式均有效：

```bash
# 环境变量方式
export XHS_ACCOUNT="13812345678"
export MCP_LOG_LEVEL="DEBUG"

# 命令行方式1
python -m mcp_xhs_publisher --account 13812345678 --log-level DEBUG

# 命令行方式2
python -m mcp_xhs_publisher --xhs_account 13812345678 --loglevel DEBUG
```

开发者可直接使用这些工具函数在自己的模块中加载配置，而不需要重复实现配置解析逻辑。

## MCP 服务器工具说明

本项目是基于 Model Context Protocol (MCP) 规范实现的服务器，提供了一组用于小红书发布的工具和资源。

### 工具注册与机制

服务器通过 Model Context Protocol 暴露工具和资源，供 Claude、Zed 等 LLM 应用发现和使用。每个工具都定义了：

- **参数规范**：工具调用需要的参数及其类型
- **返回值类型**：操作结果的数据结构
- **文档描述**：详细说明工具的用途和使用方法

### 已注册工具列表

#### 发布工具

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `publish_text` | 发布纯文本笔记 | `content`, `topics?`, `account?` |
| `publish_image` | 发布图文笔记 | `content`, `image_paths`, `topics?`, `account?` |
| `publish_video` | 发布视频笔记 | `content`, `video_path`, `cover_path?`, `topics?`, `account?` |

#### 资源 (Resources)

| 资源 URI 模式 | 描述 | 参数 |
|--------------|------|------|
| `xhs-note://{note_id}` | 获取笔记元数据 | `note_id`, `account?` |
| `xhs-user://{account}` | 获取用户信息 | `account?` |

### 工具参数与返回值

#### 1. 发布纯文本笔记

**参数**:
- `content`: 笔记文本内容
- `topics`: (可选) 话题关键词列表
- `account`: (可选) 账号标识，默认为 "default"

**返回示例**:
```json
{
    "status": "success",
    "type": "text",
    "result": {
        "note_id": "123456789",
        "time": "2023-06-01 12:34:56"
    }
}
```

#### 2. 发布图文笔记

**参数**:
- `content`: 笔记文本内容
- `image_paths`: 图片路径列表，支持本地路径和URL链接
- `topics`: (可选) 话题关键词列表
- `account`: (可选) 账号标识，默认为 "default"

**返回示例**:
```json
{
    "status": "success",
    "type": "image",
    "result": {
        "note_id": "987654321",
        "time": "2023-06-01 15:30:00",
        "image_count": 2
    }
}
```

#### 3. 发布视频笔记

**参数**:
- `content`: 笔记文本内容
- `video_path`: 视频文件路径
- `cover_path`: (可选) 封面图片路径
- `topics`: (可选) 话题关键词列表
- `account`: (可选) 账号标识，默认为 "default"

**返回示例**:
```json
{
    "status": "success",
    "type": "video",
    "result": {
        "note_id": "567891234",
        "time": "2023-06-01 16:45:00",
        "duration": "00:01:30"
    }
}
```

### 实现说明

- 路径参数可以是本地文件路径或URL
- URL图片会自动下载并处理
- 发布失败时会返回包含详细错误信息的响应
- 工具实现遵循MCP规范

## 在 LLM 应用中配置

### Claude.app 配置

在 Claude.app 设置中添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "xhs-publisher": {
      "command": "uvx",
      "args": ["mcp-xhs-publisher"],
      "env": {
        "MCP_LOG_LEVEL": "INFO",
        "XHS_ACCOUNT": "13812345678",
        "XHS_COOKIE_DIR": "~/.xhs_cookies",
        "XHS_SIGN_URL": "https://example.com/sign"
      }
    }
  }
}
```

### Cursor 配置

在 Cursor 编辑器中添加 MCP 服务器配置：

1. 点击左下角的个人资料图标
2. 选择"设置"(Settings)
3. 搜索"MCP"或导航至"AI 设置"部分
4. 添加新的 MCP 服务器配置：

```json
{
  "mcpServers": {
    "xhs-publisher": {
      "command": "uvx",
      "args": ["mcp-xhs-publisher"],
      "env": {
        "MCP_LOG_LEVEL": "INFO",
        "XHS_ACCOUNT": "13812345678",
        "XHS_COOKIE_DIR": "~/.xhs_cookies",
        "XHS_SIGN_URL": "https://example.com/sign"
      }
    }
  }
}
```

### Cline 配置

在 Cline CLI 工具中配置 MCP 服务器：

1. 编辑 Cline 配置文件 (`~/.config/cline/config.json` 或 Windows 上的 `%APPDATA%\cline\config.json`)
2. 在配置文件中添加：

```json
{
  "mcpServers": {
    "xhs-publisher": {
      "command": "uvx",
      "args": ["mcp-xhs-publisher"],
      "env": {
        "MCP_LOG_LEVEL": "INFO",
        "XHS_ACCOUNT": "13812345678",
        "XHS_COOKIE_DIR": "~/.xhs_cookies",
        "XHS_SIGN_URL": "https://example.com/sign"
      }
    }
  }
}
```

3. 使用时可通过 `--mcp xhs-publisher` 参数指定使用该服务器

### Zed 配置

在 Zed 编辑器设置中添加 MCP 服务器：

```json
{
  "mcp": {
    "servers": {
      "xhs-publisher": {
        "command": "uvx",
        "args": ["mcp-xhs-publisher"],
        "env": {
          "MCP_LOG_LEVEL": "INFO",
          "XHS_ACCOUNT": "13812345678",
          "XHS_COOKIE_DIR": "~/.xhs_cookies",
          "XHS_SIGN_URL": "https://example.com/sign"
        }
      }
    }
  }
}
```

## 账号与 cookie 管理

- 多账号支持：cookie 自动存储于 `~/.xhs_cookies/{account}.cookie`
- 首次使用时自动触发扫码登录
- 自动检测 cookie 有效性，失效时自动重新登录

## 开发指南

项目遵循标准 MCP 服务器结构，代码组织如下：

```
src/mcp_xhs_publisher/
├── __init__.py
├── __main__.py          # 入口点
├── config.py            # 配置管理
├── models/              # 数据模型
├── resources/           # MCP资源实现
├── services/            # 外部服务客户端
├── tools/               # MCP工具实现
└── util/                # 工具函数
```

### 本地开发环境设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装pre-commit钩子
pre-commit install
```

## 参考

- [Model Context Protocol 规范](https://modelcontextprotocol.io/docs/concepts/architecture)
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- [coze-mcp-server](https://github.com/coze-dev/coze-mcp-server)
- [xhs 官方文档](https://reajason.github.io/xhs/basic.html)

## 许可证

MIT 