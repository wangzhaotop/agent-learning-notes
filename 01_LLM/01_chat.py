# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 0:39


# while 循环 + 列表存历史,实现连续聊天。

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)
MODEL = os.environ.get("MODEL_NAME")

messages = []

print(f"模型:{MODEL}(输出exit退出)")

while True:
    user_input = input("\n你: ").strip()
    if user_input.lower() == "exit":
        break
    if not user_input:
        continue;

    # 1 将用户的这句话加入到消息中
    messages.append({"role": "user", "content": user_input})

    # 2 把[全部历史发给大模型 ]
    response = client.chat.completions.create(model=MODEL, messages=messages)
    reply = response.choices[0].message.content

    # AI的回复也能记录到历史消息中:
    messages.append({"role": "assistant", "content": reply})

    print(f"AI:{reply}")
