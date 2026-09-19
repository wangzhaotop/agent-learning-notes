# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 11:08


# `/save` `/load` 把对话历史存进文件、恢复回来,退出时自动保存

import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)
MODEL = os.environ.get("MODEL_NAME")

SYSTEM_PROMPT = "你是一个简洁友好的中文编程学习助手。默认回答简短,用户明确要求时才展开。"
MAX_HISTORY = 20  # 除 system 外,最多发给模型的消息条数(最近 10 轮)
SAVE_FILE = "chat_history.json"  # 对话记录存这个文件


def load_history():
    """"从文件恢复历史; 文件不存在就返回只带system 的新列表"""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def save_history(msgs):
    """把整个历史列表写进文件"""
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)


messages = load_history()

print(f"模型:{MODEL} | 命令:/save /load /reset,exit 退出")
while True:
    try:
        user_input = input("\n你: ").strip()
    except(KeyboardInterrupt, EOFError):
        print("\n再见")
        break

    if user_input.lower() == "exit":
        save_history(messages)
        print("(已自动保存)")
        break
    if user_input == "/reset":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("(历史已清空)")
        continue
    if user_input == "/save":
        save_history(messages)
        print(f"(已保存到 {SAVE_FILE})")
        continue
    if user_input == "/load":
        messages = load_history()
        print(f"已加载{len(messages)}条消息")
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
