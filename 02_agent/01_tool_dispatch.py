# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 20:11

# **目标**:把第 1 课的手动步骤封装成 `run_tool_calls()`,配一张"名字 → 函数"映射表,再让一个问题能连续多轮点菜。

import os
import json
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)

MODEL = os.environ.get("MODEL_NAME")

print(datetime.now().strftime("%Y-%m-%d %H:%M:%S %A"))


# ---- 三个真实工具 ----
def get_current_time():
    """获取当前的日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


def write_file(path, content):
    """把文本内容写入指定文件(覆盖原内容)"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"已写入 {path},共 {len(content)} 个字符"


def read_file(path):
    """读取指定文件的全部文本内容"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---- 向模型介绍这三个工具 ----
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

# --- 名字 -> 函数 映射表:调度器的核心
TOOL_IMPLS = {
"get_current_time": get_current_time,
    "write_file": write_file,
    "read_file": read_file,
}


def run_tool_calls(assistant_msg,history):
    """执行模型点 的所有工具 , 每个结果作为 role=tool 消息追加历史"""
    for tool_call in assistant_msg.tool_calls:
        name = tool_call.function.name

        #兜底 1:参数解析失败就当空参数
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        func = TOOL_IMPLS.get(name)
        if func is None:
            #兜底 2: 模型点了一道菜单上没有的菜
            result = f"错误:不存在名为 {name} 的工具"
        else:
            try:
                result = func(**args)
            except Exception as e:
                # 兜底 3:执行出错不崩程序,把错误告诉模型,它会自己调整
                result = f"工具执行出错:{e}"

        print(f"[工具]{name}({args}) ->{result}")
        history.append({
            "role":"tool",
            "tool_call_id":tool_call.id,
            "content":str(result)
        })

# ---- 一个可能连续点菜的问题:先写文件,再读回来确认 ----
messages = [{"role": "user", "content": "帮我在 todo.txt 里记一条:明天上午十点开会。记完后读一下这个文件,向我确认内容。"}]

for round_i in range(5):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools
    )

    msg = response.choices[0].message
    messages.append(msg.model_dump(exclude_none=True))

    if not msg.tool_calls:  # 没有点菜 = 给出最终回答了
        print(f"最终回答:{msg.content}")
        break

    print(f" --- 第 {round_i+1} 轮工具调用 ---")
    run_tool_calls(msg,messages)

else:
    # 5 轮全在点菜、没 break 出来,强制停止(防失控)
    print("连续 5 轮都在调工具,强制停止")

