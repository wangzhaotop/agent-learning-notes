"""05_mcp/mcp_client.py —— 同步壳包异步,多 server 动态发现"""
import asyncio
import threading

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolbox:
    """
    一次性连上多个 MCP server,把它们的工具变成 Agent 能用的工具表。
        内部:一条后台线程跑 asyncio 事件循环,MCP 会话常驻其中;
        对外:全是同步方法,阶段 4 的同步 Agent 一行都不用改。
    """

    def __init__(self, servers: dict):
        # 前缀 -> StdioServerParameters
        # {
        #     "time": StdioServerParameters(command=sys.executable, args=["time_server.py"]),
        #     "file": StdioServerParameters(command=sys.executable, args=["file_server.py"]),
        # }
        self.servers = servers
        # 后台事件循环对象，__enter__ 里创建
        self._loop = None
        # _thread：后台线程对象，跑 _run
        self._thread = None
        # 前缀 -> ClientSession，每个 MCP 服务器一个会话
        self._sessions = {}
        self._tools = {}
        # threading.Event，用来让主线程等后台线程把会话建好
        self._ready = threading.Event()
        # 用来通知后台协程退出
        self._close = None

    # ---- 生命周期 -----
    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=60):
            raise RuntimeError("MCP 会话建立超时:检查 server 脚本路径")
        return self

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        from contextlib import AsyncExitStack

        async with AsyncExitStack() as stack:
            for key, params in self.servers.items():
                read, write = await stack.enter_async_context(stdio_client(params))
                session = await stack.enter_async_context(ClientSession(read, write))
                init = await session.initialize()
                print(f"(已连上 MCP server:{key} -> {init.server_info.name} "
                      f"{init.server_info.version},协议 {init.protocol_version})")
                self._sessions[key] = session

            # 动态发现: 工具表完全来自server 代码里一个名字都没写死
            for key, session in self._sessions.items():
                listed = await session.list_tools()
                for t in listed.tools:
                    self._tools[f"{key}__{t.name}"] = (key, t.name, t)

            self._close = asyncio.Event()
            self._ready.set()
            await self._close.wait()

    def __exit__(self, *exc):
        if self._close and self._loop:
            self._loop.call_soon_threadsafe(self._close.set)
        if self._thread:
            self._thread.join(timeout=10)
        if self._loop:
            self._loop.close()
        return False

    # ---------- 同步 API(Agent 只认这三个) ----------
    def _await(self, coro):
        """把协程扔进后台事件循环,自己在当前线程等结果——Java:Future.get()"""
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=120)

    def get_openai_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": public,
                    "description": t.description or "",
                    "parameters": t.input_schema  # 协议给的 Schema 直接用
                }
            }
            for public, (_, _, t) in self._tools.items()
        ]

    def call_tool(self, public_name, args):
        entry = self._tools.get(public_name)
        if entry is None:
            return f"错误:不存在名为{public_name}的工具"
        key, real_name, _ = entry
        try:
            result = self._await(self._sessions[key].call_tool(real_name, args))
        except Exception as e:
            return f"工具执行出错:{e}"
        text = "\n".join(getattr(c, "text", str(c)) for c in result.content)
        return ("工具执行出错:" if result.is_error else "") + text

    def tool_names(self):
        return list(self._tools)
