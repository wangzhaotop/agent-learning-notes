# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 17:06
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)
MODEL = os.environ.get("MODEL_NAME")


# 先定一一个工具
def get_current_time():
    """获取当前的日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


# ---- 第 2 步:用 JSON Schema 向模型"介绍"这个工具 ----
# description 写得越清楚,模型越知道什么时候该用它
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间",
            "parameters": {
                "type": "object",
                "properties": {},  # 这个工具不需要参数
                "required": [],
            },
        },
    }
]

# ---- 第3步: 发消息,带上工具说明书 ----
messages = [{"role": "user", "content": "现在几点了?"}]
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=tools,
)
msg = response.choices[0].message

# ---- 第 4 步:亲眼看看模型的"点菜单" ----
if not msg.tool_calls:
    # 模型有权不调用工具直接回答——什么时候调、什么时候不调,是它自己判断的
    print("模型没有调用工具,直接回答了:", msg.content)
    raise SystemExit

print("=== 模型想调用的工具 ===")
print(msg.tool_calls)  # 此时 msg.content 往往是 None,回复藏在 tool_calls 里

tool_call = msg.tool_calls[0]
print(f"工具名:{tool_call.function.name}")

# ★ 大坑:arguments 不是字典,是【JSON 字符串】!
print(f"原始参数:{tool_call.function.arguments}(类型:{type(tool_call.function.arguments)})")
args = json.loads(tool_call.function.arguments)
print(f"解析后的参数:{args}")

# --- 第5步: 你的代码执行工具
result = get_current_time(**args)
print(f"执行结果:{result}")

# 把刚刚问的问题 和工具执行的记录都返回给大模型 让大模型基于工具调用的记录去执行
print(msg.model_dump(exclude_none=True))
messages.append(msg.model_dump(exclude_none=True))
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": result
})

final = client.chat.completions.create(
    model=MODEL,
    messages=messages
)
print(f"模型最终回答:{final.choices[0].message.content}")
