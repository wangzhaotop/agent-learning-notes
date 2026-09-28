"""所有 LLM 调用的唯一出口,自带成本账本。单价是示例,按你平台价目表改"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)
CHAT_MODEL = os.environ.get("MODEL_NAME")

PRICE_IN, PRICE_OUT = 2.0, 8.0  # 示例单价(元/百万 token)
BILL = {"calls": 0, "in": 0, "out": 0, "cost": 0.0}


def chat(messages, **kwargs):
    """记账版聊天:返回 (回复文本, usage)"""
    resp = client.chat.completions.create(model=CHAT_MODEL, messages=messages, **kwargs)
    u = resp.usage
    BILL['calls'] += 1
    BILL['in'] += u.prompt_tokens
    BILL['out'] += u.completion_tokens
    BILL['cost'] += u.prompt_tokens / 1e6 * PRICE_IN + u.completion_tokens / 1e6 * PRICE_OUT
    return resp.choices[0].message.content, u


def bill():
    return (f"账单:调用 {BILL['calls']} 次 | 输入 {BILL['in']} tok | "
            f"输出 {BILL['out']} tok | 约 ¥{BILL['cost']:.4f}")


