"""Agent 循环:点菜 → 执行 → 喂回,直到给出最终回答。不藏任何全局状态"""
import json

import llm_client
from tools import call_tool, get_openai_tools

MAX_STEPS = 10


def run_tool_calls(tool_calls, history):
    """执行模型点的所有菜(现在是纯字典,不再依赖 SDK 对象)"""
    for tc in tool_calls:
        name = tc["function"]["name"]
        try:
            args = json.loads(tc["function"]["arguments"])
        except json.JSONDecodeError:
            args = {}

        result = call_tool(name, args)
        print(f"[工具] {name}({args}) -> {result}")
        history.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})


def reply(user_input, history):
    """处理一句话:循环点菜直到最终回答。history 由调用方持有并原地追加"""
    history.append({"role": "user", "content": user_input})
    for _ in range(MAX_STEPS):
        content,tool_calls = llm_client.chat_stream(history, tools=get_openai_tools())

        if tool_calls:
            # 注意:append 的是 dict 本身,别再套一层 []——套了就成"历史里躺着一个列表"
            history.append({"role": "assistant", "content": content or None,
                            "tool_calls": tool_calls})
            run_tool_calls(tool_calls, history)
        else:
            history.append({"role":"assistant","content":content})
            # 表示没有工具调用可以直接返回了
            return content
    return "(达到最大步数,强制停止)"
