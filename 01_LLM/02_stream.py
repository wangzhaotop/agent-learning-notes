# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 0:47

# AI 一边生成一边往外蹦字;用 system 消息控制人设

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)
MODEL = os.environ.get("MODEL_NAME")

SYSTEM_PROMPT = "你是一个简洁友好的中文编程学习助手。默认回答简短,用户明确要求时才展开。"

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print(f"模型:{MODEL}(输入exit退出)")
while True:
    try:
        user_input = input("\n你: ").strip()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C / Ctrl+D 时优雅退出,而不是甩一屏报错
        print("\n再见!")
        break

    if user_input.lower() == "exit":
        break
    if not user_input:
        continue

    messages.append({"role": "user", "content": user_input})

    print("AI: ", end="", flush=True)
    reply_parts = []  # 收集所有碎片,最后拼成完整回复

    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True, temperature=0.7)

    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            print(delta, end="", flush=True)
            reply_parts.append(delta);
    print()

    # 碎片拼成完整回复 存进历史
    messages.append({"role": "assistant", "content": "".join(reply_parts)})
