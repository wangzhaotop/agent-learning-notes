"""第 7 课:给 llm_client.chat_stream 一份"固定剧本",Agent 循环 0 token 跑"""
import json

import agent


def stream(content="", tool_calls=None):
    """伪造 llm_client.chat_stream 的返回:(content, tool_calls)"""
    return content, tool_calls or []


def tool_call(name="get_current_time", args="{}", call_id="call_1"):
    """伪造一个点菜单——注意是 llm_client 攒出来的新结构:function 包层"""
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": args},
    }


def test_一轮直达_不点菜(monkeypatch):
    monkeypatch.setattr(agent.llm_client, "chat_stream",
                        lambda *a, **k: stream("今天星期四"))
    messages = [{"role": "system", "content": "sys"}]
    assert agent.reply("你好", messages) == "今天星期四"
    assert messages[-1]["role"] == "assistant"


def test_点菜_执行_再回答(monkeypatch):
    plan = iter([
        stream("", [tool_call("get_current_time")]),   # 第一轮:点菜
        stream("现在是下午三点"),                       # 第二轮:给答案
    ])
    monkeypatch.setattr(agent.llm_client, "chat_stream", lambda *a, **k: next(plan))

    messages = [{"role": "system", "content": "sys"}]
    assert agent.reply("现在几点", messages) == "现在是下午三点"

    # assistant 消息必须是 dict(不是被 [] 套住的 list),否则下一轮请求直接 400
    assert isinstance(messages[2], dict)
    assert messages[2]["tool_calls"][0]["function"]["name"] == "get_current_time"
    assert messages[3]["role"] == "tool"                       # 菜喂回去了
    assert messages[3]["tool_call_id"] == "call_1"             # 回执认领了这次调用
    assert messages[4]["content"] == "现在是下午三点"            # 最终回答入历史


def test_工具参数是JSON碎片_也能解析(monkeypatch, tmp_path):
    # 写文件落到 tmp_path,别把测试产物扔进项目目录
    target = tmp_path / "笔记.txt"
    args = json.dumps({"path": str(target), "content": "hi"}, ensure_ascii=False)
    plan = iter([
        stream("", [tool_call("write_file", args)]),
        stream("写好了"),
    ])
    monkeypatch.setattr(agent.llm_client, "chat_stream", lambda *a, **k: next(plan))
    messages = [{"role": "system", "content": "sys"}]
    assert agent.reply("写个文件", messages) == "写好了"
    assert messages[2]["tool_calls"][0]["function"]["arguments"].startswith("{")
    assert "已写入" in messages[3]["content"]                   # 工具真的跑了
    assert target.read_text(encoding="utf-8") == "hi"           # 而且写对了地方


def test_参数不是合法JSON_兜底成空参(monkeypatch):
    plan = iter([
        stream("", [tool_call("get_current_time", "这不是JSON")]),
        stream("时间给你了"),
    ])
    monkeypatch.setattr(agent.llm_client, "chat_stream", lambda *a, **k: next(plan))
    messages = [{"role": "system", "content": "sys"}]
    assert agent.reply("几点", messages) == "时间给你了"
    assert messages[3]["role"] == "tool"                        # 没崩,继续走完循环


def test_点不存在的菜_兜底后继续(monkeypatch):
    plan = iter([
        stream("", [tool_call("no_such_tool")]),
        stream("那个工具没有,抱歉"),
    ])
    monkeypatch.setattr(agent.llm_client, "chat_stream", lambda *a, **k: next(plan))
    messages = [{"role": "system", "content": "sys"}]
    assert agent.reply("掷骰子", messages) == "那个工具没有,抱歉"
    assert "不存在" in messages[3]["content"]                   # 兜底文本喂回了模型


def test_超过最大步数_强制停止(monkeypatch):
    monkeypatch.setattr(agent.llm_client, "chat_stream",
                        lambda *a, **k: stream("", [tool_call()]))
    monkeypatch.setattr(agent, "MAX_STEPS", 3)
    messages = [{"role": "system", "content": "sys"}]
    assert "最大步数" in agent.reply("几点", messages)
