"""05_mcp/async_lab.py —— 异步补课实验:5 个小实验,全部零依赖,总耗时约 8 秒
配套文档:异步补课.md(每个实验对应文档的一个结论)"""
import asyncio
import threading
import time


def ts():
    return time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"


def log(msg):
    print(f"[{ts()}] {msg}")


# ---------- 实验 1:顺序 await vs asyncio.gather ----------
async def fetch(name, seconds):
    """模拟一次 I/O:等待后返回。注意用 asyncio.sleep,不是 time.sleep"""
    await asyncio.sleep(seconds)
    return f"{name} 完成"


async def lab1_sequential():
    log("实验1a:顺序 await 三次(每次 1 秒)")
    r1 = await fetch("A", 1)
    r2 = await fetch("B", 1)
    r3 = await fetch("C", 1)
    log(f"  {r1} / {r2} / {r3}")


async def lab1_concurrent():
    log("实验1b:asyncio.gather 三个一起(总共约 1 秒)")
    results = await asyncio.gather(fetch("A", 1), fetch("B", 1), fetch("C", 1))
    log(f"  {results}")


# ---------- 实验 2:async 里 time.sleep 卡死整个事件循环 ----------
async def heartbeat():
    """心跳:每 0.3 秒打一次点,证明 loop 活着"""
    for _ in range(8):
        await asyncio.sleep(0.3)
        log("  心跳 tick")


async def blocking_task():
    log("实验2:阻塞任务开始(time.sleep 2 秒 —— 罪魁祸首)")
    time.sleep(2)                 # ★ 错误示范:阻塞了 loop 所在线程
    log("实验2:阻塞任务结束")


async def lab2():
    log("实验2:心跳 + 阻塞任务同跑 —— 盯紧心跳有没有断")
    await asyncio.gather(heartbeat(), blocking_task())
    log("实验2结论:心跳断档 2 秒 —— time.sleep 卡死的是整个事件循环(罚全队)")


# ---------- 实验 3:asyncio.to_thread 是阻塞的逃生门 ----------
def blocking_io():
    time.sleep(2)
    return "阻塞 I/O 完成(跑在线程池里)"


async def lab3():
    log("实验3:同样的阻塞函数,用 asyncio.to_thread 丢进线程池")
    await asyncio.gather(heartbeat(), asyncio.to_thread(blocking_io))
    log("实验3结论:心跳全程没断 —— 阻塞的只有线程池里那个线程")


# ---------- 实验 4:忘记 await = 什么都没发生 ----------
async def lab4():
    log("实验4:调用 async 函数但忘了 await")
    coro = fetch("被遗忘的任务", 1)     # 只是创建了协程对象,一行没执行
    log(f"  coro = {coro}")
    log("  (稍后在警告里找:RuntimeWarning: coroutine 'fetch' was never awaited)")


# ---------- 实验 5:迷你 MCPToolbox —— 后台线程跑 loop 的同步桥 ----------
async def async_tool(name):
    """模拟一次 MCP 工具调用:等 0.5 秒返回"""
    await asyncio.sleep(0.5)
    return f"{name} 的结果"


class MiniToolbox:
    """你的 mcp_client.py 的最小复刻:同步世界 ↔ 异步世界的桥"""

    def __init__(self):
        self._loop = None
        self._thread = None
        self._ready = threading.Event()   # ≈ Java CountDownLatch
        self._close = None

    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=10)      # 主线程等异步世界就绪
        return self

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self):
        log("实验5:异步世界就绪(会话常驻中…)")
        self._close = asyncio.Event()
        self._ready.set()
        await self._close.wait()          # 常驻:直到收到关闭信号

    def _await(self, coro):
        """把协程投到后台 loop,当前线程等结果 —— Java: Future.get()"""
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=30)

    def call_tool(self, name):
        return self._await(async_tool(name))

    def __exit__(self, *exc):
        self._loop.call_soon_threadsafe(self._close.set)   # 线程安全地叫停
        self._thread.join(timeout=10)
        self._loop.close()
        log("实验5:异步世界已关闭")
        return False


def lab5():
    log("实验5:同步主线程里用 MiniToolbox(模拟你的 agent_main.py)")
    with MiniToolbox() as box:
        log(f"  调用1:{box.call_tool('查时间')}")
        log(f"  调用2:{box.call_tool('读文件')}")
    log("实验5结论:同步代码零感知,异步会话常驻在后台线程")


if __name__ == "__main__":
    t0 = time.time()
    asyncio.run(lab1_sequential())
    asyncio.run(lab1_concurrent())
    asyncio.run(lab2())
    asyncio.run(lab3())
    asyncio.run(lab4())
    lab5()
    log(f"全部实验完成,总耗时 {time.time() - t0:.1f} 秒")
