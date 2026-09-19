"""
**目标**:加上 `input()` 对话循环和跨轮记忆。**Agent = LLM + 工具 + while 循环**,
写完这个,你就拥有一个完整的、不依赖任何框架的 Agent。
"""

import os
import json
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)

model_name = os.environ.get("MODEL_NAME")


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入{path} 共{len(content)}个字符"


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "把文本内容写入指定文件,覆盖原内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文本内容"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的全部文本内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

TOOL_IMPLS = {
    "get_current_time": get_current_time,
    "write_file": write_file,
    "read_file": read_file
}


def run_tool_calls(assistant_msg, history):
    for tool_call in assistant_msg.tool_calls:
        name = tool_call.function.name

        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        func = TOOL_IMPLS.get(name)

        if func is None:
            result = f"错误:不存在名为{name}的工具"
        else:
            try:
                result = func(**args)
            except Exception as e:
                result = f"工具执行出错:{e}"

        print(f"[工具] {name}({args}) -> {result}")

        history.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })


# Agent部分
SYSTEM_PROMPT = "你是一个能使用工具的助手。需要查时间、读写文件时调用相应工具;回答保持简洁。"
MAX_STEPS = 10  # 单次提问最多允许的"点菜"轮数

messages = [{"role": "system", "content": SYSTEM_PROMPT}]


def agent_reply(user_input):
    messages.append({"role": "user", "content": user_input})

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools
        )

        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content
        run_tool_calls(msg, messages)

    return "(达到最大步数,强制停止)"


print(f"Agent 已启动,模型:{model_name}(exit 退出)")

while True:
    try:
        user_input = input("\n你: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n再见")
        break

    if user_input.lower() == "exit":
        break
    if not user_input:
        continue

    reply = agent_reply(user_input)
    print(f"AI:{reply}")
