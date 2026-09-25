import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

chat_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)
CHAT_MODEL = os.environ.get("MODEL_NAME")

embed_client = OpenAI(
    api_key=os.environ.get("EMBEDDING_API_KEY"),
    base_url=os.environ.get("EMBEDDING_BASE_URL"),
)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")


def chat(messages, tools=None, **kwargs):
    """非流式聊天,返回 SDK 响应对象;kwargs 原样透传(比如 response_format)"""
    return chat_client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, tools=tools, **kwargs
    )


def embed_texts(texts, batch_size=32):
    """批量向量化,一次最多 32 条"""
    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        resp = embed_client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in resp.data)
    return vectors