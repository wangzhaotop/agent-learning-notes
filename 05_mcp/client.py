"""05_mcp/client.py —— 手写 MCP client:握手 → 发现 → 调用"""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(command=sys.executable, args=
["file_server.py"])


async def main():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            # 1.握手
            init = await session.initialize()
            print("握手成功:", init.server_info.name, init.server_info.version)
            print("协议版本:", init.protocol_version)

            # 2 发现工具
            tools = await session.list_tools()
            print("\n 发现工具:")
            for t in tools.tools:
                print(f"    -{t.name}:{t.description}")
                print(f"        input_schema = {t.input_schema}")

            # 调用工具
            print("\n调用 get_current_time:")
            result = await session.call_tool("get_current_time", {})
            print("  is_error =", result.is_error)
            print("  content =", [c.text for c in result.content])

            # 错误是数据，不是异常
            print("\n 调用不存在的工具:")
            bad = await session.call_tool("no_such_tool", {})
            print(" is_error =", bad.is_error, "|", bad.content[0].text)


if __name__ == '__main__':
    asyncio.run(main())
