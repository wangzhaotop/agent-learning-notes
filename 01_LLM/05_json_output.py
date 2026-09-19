# -*- coding: utf-8 -*-
# @Author   : WangZZZ
# @Date     : 2026/9/19 15:23


# 让模型输出**固定格式的 JSON** 并解析出字段。这是从"陪聊"到"程序可靠用模型"的分水岭——阶段 2 Agent 调工具全靠它。

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)

MODEL = os.environ.get("MODEL_NAME")

SYSTEM_PROMPT = (
    "你是 JSON 生成器。不管用户说什么,只返回一个 JSON 对象:"
    '{"answer": "对用户问题的简短回答", "mood": "happy/sad/angry/neutral 之一"}。'
    "不要输出 JSON 以外的任何文字。"
)

print(f"模型:{MODEL}(输出 exit 退出)")

while True:
    user_input = input("\n你: ").strip()
    if user_input.lower() == "exit":
        break
    if not user_input:
        continue

    responses = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        response_format={"type":"json_object"}
    )
    raw = responses.choices[0].message.content

    # 模型偶尔会不听话,解析失败不能让程序崩,所以 try/except 包住
    try:
        data = json.loads(raw)
        print(f"回答:{data['answer']}")
        print(f"情绪: {data['mood']}")
    except json.JSONDecodeError:
        print(f"模型没按要求返回 JSON,原文是:\n{raw}")
