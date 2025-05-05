from mcp.server.fastmcp import FastMCP
from mcp_xhs_publisher.mcp_tools import register_tools
# 假定官方 SDK
# from mcp_sdk.server import MCPServer

def main():
    mcp = FastMCP("mcp-xhs-publisher")
    register_tools(mcp)
    mcp.run()

if __name__ == "__main__":
    main() 