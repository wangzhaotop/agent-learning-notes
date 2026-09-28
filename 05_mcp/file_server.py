"""05_mcp/file_server.py —— 阶段 4 的三个文件工具,搬进独立进程"""
import sys
from datetime import datetime

from mcp.server.mcpserver import MCPServer

server = MCPServer(name="file_tools", version="0.1.0", instructions="阶段 4 的三个文件工具")


@server.tool()
def get_current_time():
    """获取当前的日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


@server.tool()
def write_file(path: str, content: str) -> str:
    """把文本内容写入指定文件(覆盖原文件)"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入{path}共{len(content)}个字符"


@server.tool()
def read_file(path: str) -> str:
    """读取指定文件的内容"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# 追加:resources 与prompts
@server.resource("study://handbook")
def handbook() -> str:
    """学习手册目录速览"""
    return "# 学习手册\n- 01_LLM\n- 02_agent\n- 03_rag\n- 04_engineering\n- 05_mcp"

@server.prompt()
def review(topic:str) -> str:
    """生成一组复习提问"""
    return f"请用3个问题考我:{topic},每题只答不问。"

if __name__ == "__main__":
    # 日志一律走 stderr:stdout 是协议通道
    print("file-tools 已启动(stdio)", file=sys.stderr)
    server.run()  # 默认 transport="stdio"