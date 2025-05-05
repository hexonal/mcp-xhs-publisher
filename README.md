# mcp-xhs-publisher

小红书自动发布的 Model Context Protocol (MCP) 工具，支持文本、图文、视频笔记一键发布。

## 特性
- 支持扫码登录与多账号 cookie 管理
- 支持纯文本、图文、视频笔记自动发布
- 完全对齐 MCP Server 规范，便于 Claude、Zed 等 LLM Host 集成
- 代码风格参考 coze-mcp-server

## 安装

推荐 Python 3.11 及以上：

```bash
pip install xhs requests pydantic
# 如需官方 mcp sdk:
# pip install mcp-sdk
```

## 启动 MCP Server

```bash
python -m mcp_xhs_publisher.main
```

或使用 uvx/uv：

```bash
uvx mcp_xhs_publisher.main
```

## 工具注册与调用

- 所有发布相关工具已自动注册到 MCP Server
- 支持 publish_text、publish_image、publish_video 三种发布方式
- 参数支持通过环境变量、命令行参数、MCP 工具参数灵活传递

## 账号与 cookie 管理

- 支持多账号，cookie 自动存储于 ~/.xhs_cookies/{account}.cookie
- 支持扫码登录，自动检测 cookie 有效性

## 参考
- [coze-mcp-server](https://github.com/coze-dev/coze-mcp-server)
- [xhs 官方文档](https://reajason.github.io/xhs/basic.html)

## License
MIT 