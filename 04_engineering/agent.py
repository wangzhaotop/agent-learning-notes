"""Agent 循环:点菜 → 执行 → 喂回,直到给出最终回答。不藏任何全局状态"""
import json

import llm_client
from tools import call_tool, get_openai_tools

MAX_STEPS = 10


def run_tool_calls(assistant_msg, history):
    for tool_call in assistant_msg.tool_calls:
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        result = call_tool(name, args)
        print(f"[工具] {name}({args}) -> {result}")
        history.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(result)})


def reply(user_input, history):
    """处理一句话:循环点菜直到最终回答。history 由调用方持有并原地追加"""
    history.append({"role": "user", "content": user_input})
    for _ in range(MAX_STEPS):
        response = llm_client.chat(history, tools=get_openai_tools())
        msg = response.choices[0].message
        history.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content
        run_tool_calls(msg, history)
    return "(达到最大步数,强制停止)"
