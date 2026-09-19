# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 15:30


"""
**不看本手册任何一行**,从空文件写一个聊天机器人,要求:

- [ ] 多轮对话 + system prompt
- [ ] 流式输出
- [ ] 历史窗口(MAX_HISTORY 裁剪)
- [ ] `/save` `/load` `/reset` 三个命令,退出自动保存

"""

import os
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)

MODEL = os.environ.get("MODEL_NAME")
SYSTEM_PROMPT = "你是一个AI聊天助手,请用简短的语言进行交流"
MAX_HISTORY = 20
SAVE_FILE = "chat_history.json"


def save_history(msgs):
    """把历史消息写入文件中"""
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)


def load_history():
    """从文件中加载历史消息"""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return [{"role": "system", "content": SYSTEM_PROMPT}]


messages = load_history()

print(f"模型:{MODEL} (/save` `/load` `/reset` 三个命令,退出自动保存)")

while True:
    try:
        user_input = input("\n你: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("强行退出")
        break
    if user_input.lower() == "exit":
        save_history(messages)
        print("已自动保存")
        break
    if user_input == "/reset":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("(历史已清空)")
        continue
    if user_input == "/load":
        messages = load_history()
        print(f"已加载{len(messages)}条消息")
        continue
    if user_input == "/save":
        save_history(messages)
        print(f"(已保存到 {SAVE_FILE})")
        continue
    if not user_input:
        continue

    messages.append({"role": "user", "content": user_input})
    to_send = [messages[0]] + messages[1:][-MAX_HISTORY:]

    print("AI: ", end="", flush=True)
    reply_parts = []
    stream = client.chat.completions.create(
        model=MODEL,
        messages=to_send,
        stream=True,
        temperature=0.7
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            print(delta, end="", flush=True)
            reply_parts.append(delta)
    print(f"此次AI回答的信息:{reply_parts}")
    print()

    messages.append({"role": "assistant", "content": "".join(reply_parts)})
    print(f"历史消息更新:{messages}")
