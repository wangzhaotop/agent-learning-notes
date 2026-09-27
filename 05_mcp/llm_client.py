import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

chat_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)
CHAT_MODEL = os.environ.get("MODEL_NAME")

embed_client = OpenAI(
    api_key=os.environ.get("EMBEDDING_API_KEY"),
    base_url=os.environ.get("EMBEDDING_BASE_URL"),
)

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")


def chat(messages, tools=None, **kwargs):
    """非流式聊天,返回SDK响应对象;kwargs 原样透传(比如response_format)"""
    return chat_client.chat.completions.create(
        model=CHAT_MODEL, tools=tools, messages=messages, **kwargs
    )


def chat_stream(messages, tools=None):
    "流式聊天:边生成边打印;返回赞好的(content,tool_calls 列表)"
    stream = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        tools=tools,
        stream=True
    )
    content_parts = []
    tc_slots = {}  # index -> {"id","name","arguments"}:按碎片顺序攒
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            content_parts.append(delta.content)
        for tc in (delta.tool_calls or []):
            slot = tc_slots.setdefault(tc.index, {
                "id": "",
                "name": "",
                "arguments": "",
            })
            if tc.id:
                slot["id"] = tc.id
            if tc.function and tc.function.name:
                slot["name"] = tc.function.name
            if tc.function and tc.function.arguments:
                # 必须 += :arguments 是碎片,一段段补过来的,用 = 只剩最后一片
                slot["arguments"] += tc.function.arguments

    print()
    # 回传给API 的 tool_calls 必须带function 包层,扁平结构会被判 400
    tool_calls = [
        {
            "id": s["id"],
            "type": "function",
            "function": {
                "name": s["name"],
                "arguments": s["arguments"]
            }
        }
        for _, s in sorted(tc_slots.items())
    ]
    return "".join(content_parts), tool_calls


def embed_text(texts, batch_size=32):
    """批量向量化,一次最多32条"""
    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        resp = embed_client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in resp.data)
    return vectors
