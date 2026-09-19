# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 10:37

# 历史无限变长会撑爆上下文、烧钱。改成只发"system + 最近 N 条",加 `/reset` 命令。


import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)

model_name = os.environ.get("MODEL_NAME")

SYSTEM_PROMPT = "你是一个简洁友好的中文编程学习助手。默认回答简短,用户明确要求时才展开"
MAX_HISTORY = 20  # 除 system 外,最多发给模型的消息条数(最近 10 轮)
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print(f"模型:{model_name}| 命令:/reset 清空历史,exit 退出")

while True:
    try:
        user_input = input("\n你: ").strip()
    except(KeyboardInterrupt, EOFError):
        print("\n再见")
        break
    if user_input.lower() == "exit":
        break
    if user_input == "/reset":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        print("历史已清空")
        continue
    if not user_input:
        continue

    messages.append({"role": "user", "content": user_input})

    print("AI: ", end="", flush=True)
    reply_parts = []  # 收集所有碎片,最后拼成完整回复

    to_send = [messages[0]] + messages[1:][-MAX_HISTORY:]
    stream = client.chat.completions.create(
        model=model_name,
        messages=to_send,
        stream=True,
        temperature=0.7
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            print(delta, end="", flush=True)
            reply_parts.append(delta)
    print()
    print(f"此次收集到模型回复的信息:{reply_parts}")

    # 回复完 将消息加入到历史消息中
    messages.append({"role": "assistant", "content": "".join(reply_parts)})
    print(f"历史消息更新:{messages}")
