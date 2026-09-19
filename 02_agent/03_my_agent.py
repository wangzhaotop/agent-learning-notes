"""
- [ ] 多轮对话,记忆跨轮保留(对话式 Agent,不是一问一答)
- [ ] 至少 3 个工具,其中 **1 个是你自己从零设计的新工具**(比如:计算器、查看目录文件列表、掷骰子……自己写函数 + 自己写 JSON Schema 说明书)
- [ ] `MAX_STEPS` 防死循环
- [ ] `/reset` 清空对话(注意:清的是 messages,工具写出的文件不受影响)
- [ ] `/save` `/load` 保存恢复会话(提示:所有消息已经是 `model_dump()` 出来的字典,可以直接 `json.dump`)
- [ ] 保留 `[工具]` 执行日志
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
SAVE_FILE = "chat_history.json"
SYSTEM_PROMPT = ("你是一个AI助手，你能计算、查看目录文件、"
                 "查时间、读写文件时调用相应工具等功能。回答问题 请用简短语言进行回答")


def save_history(msgs):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)


def load_history():
    """"从文件恢复历史; 文件不存在就返回只带system 的新列表"""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入{path} 共{len(content)}个字符"


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


def calc_num(a, b):
    return float(a) + float(b)


def watch_dir(path):
    """列出指定目录下的文件和子目录"""
    try:
        entries = os.listdir(path)
    except FileNotFoundError:
        return f"错误:目录不存在 {path}"
    except NotADirectoryError:
        return f"错误:{path} 不是一个目录"
    except PermissionError:
        return f"错误:没有权限访问 {path}"
    return ",".join(entries)


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
            "name": "calc_num",
            "description": "计算两个数的和",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "第一个加数"
                    },
                    "b": {
                        "type": "number",
                        "description": "第二个加数"
                    }
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "watch_dir",
            "description": "查看路径下的目录文件列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要查看的目录路径,例如 D:/python/projectCode 或 ./notes"
                    },
                },
                "required": ["path"]
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

TOOLS_IMPLS = {
    "get_current_time": get_current_time,
    "calc_num": calc_num,
    "watch_dir": watch_dir,
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

        func = TOOLS_IMPLS.get(name)

        if func is None:
            result = f"错误, 不存在名为{name}的工具"
        else:
            try:
                result = func(**args)
            except Exception as e:
                result = f"工具执行出错:{e}"

        print(f"[工具] {name}({args}) -> {result}")

        history.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            }
        )


# Agent部分
MAX_STEPS = 10

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


print(f"Agent 已启动,模型:{model_name}(exit 退出 /reset 清空对话) /save 保存会话 /load 加载会话")

while True:
    try:
        user_input = input("\n你: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n再见")
        break

    if user_input.lower() == "exit":
        break

    if user_input == "/load":
        messages = load_history()
        print(f"已加载{len(messages)}条消息")
        continue

    if user_input == "/save":
        save_history(messages)
        print(f"(已保存到 {SAVE_FILE})")
        continue

    if user_input == "/reset":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print(f"(对话已清空,当前 {len(messages)} 条消息)")
        continue

    if not user_input:
        continue

    reply = agent_reply(user_input)
    print(f"AI:{reply}")
