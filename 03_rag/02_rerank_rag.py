import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from sentence_transformers import CrossEncoder

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)
MODEL = os.environ.get("MODEL_NAME")

# ---- 复用第 1 课的文档和切块逻辑 ----
docs = {
    "python_basics.txt": """
Python 是一门解释型、面向对象、动态类型的高级编程语言。
特点: 语法简洁、易学易用、社区活跃、库生态丰富。
常用场景: Web 开发、数据分析、机器学习、自动化脚本。
版本: Python 2 已停止维护,推荐使用 Python 3.8+。
    """.strip(),

    "agent_intro.txt": """
Agent 的核心公式: Agent = LLM + 工具 + 循环。
LLM 负责规划和决策,工具负责执行,循环让 Agent 能多步推理。
典型流程: 用户提问 → LLM 决定调哪个工具 → 执行工具 → 把结果告诉 LLM → LLM 给出最终答案。
常见坑: 工具调用死循环、上下文窗口爆炸、参数解析失败。
    """.strip(),

    "rag_concept.txt": """
RAG(Retrieval-Augmented Generation)是检索增强生成技术。
核心思路: 把文档切块向量化,用户问问题时检索相关块,塞进 prompt 给模型。
不是微调: 不改模型参数,只是"考试时允许翻书"。
关键技术: Embedding(向量化)、向量数据库(chromadb/faiss)、Rerank(重排序)。
RAG 能解决: 知识更新、私有数据、降低幻觉。
    """.strip(),

    "deepseek_info.txt": """
DeepSeek 是一家中国 AI 公司,推出了 DeepSeek-V3 和 DeepSeek-R1 等模型。
DeepSeek-V3 是通用对话模型,支持 64K 上下文窗口、工具调用、JSON 输出。
DeepSeek-R1 是推理模型,内置思考链(Chain-of-Thought),适合数学、代码等复杂推理任务。
API 兼容 OpenAI 格式,base_url 是 https://api.deepseek.com。
    """.strip()
}


def chunk_text(text: str, source_name: str):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []

    for i, para in enumerate(paragraphs):
        chunks.append({
            "text": para,
            "metadata": {"source": source_name, "chunk_id": i}
        })

    return chunks


all_chunks = []
for filename, content in docs.items():
    all_chunks.extend(chunk_text(content, filename))

print(f"切块完成:{len(all_chunks)}")

# ---- 存入 chromadb ----
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="docs_rerank")

collection.add(
    documents=[chunk["text"] for chunk in all_chunks],
    metadatas=[chunk["metadata"] for chunk in all_chunks],
    ids=[f"chunk_{i}" for i in range(len(all_chunks))]
)

print(f"已存入 chromadb, 文档数: {collection.count()}")

# ---- 第 1 步: 向量检索粗筛(取 top-10) ----
user_query = "DeepSeek 有哪些模型?"
print(f"\n用户提问: {user_query}")

results = collection.query(
    query_texts=[user_query],
    n_results=10  # 粗筛取 10 个候选(实际项目可能取 20~50)
)
print(f"搜索结果为:{results}")

retrieved_docs = results["documents"][0]
retrieved_meta = results["metadatas"][0]
distances = results["distances"][0]

print(f"向量检索粗筛: 取 top-{len(retrieved_docs)} 个候选")
for i, (doc, meta, dist) in enumerate(zip(retrieved_docs, retrieved_meta, distances)):
    print(f"  #{i + 1} 距离={dist:.4f} [{meta['source']}] {doc[:60]}...")

# ---- 第 2 步: Rerank 精排(取 top-3) ----
# 加载中文 cross-encoder 模型(第一次运行会下载,约 400MB)
reranker = CrossEncoder("BAAI/bge-reranker-base")  # 中文 rerank 模型

# 构造输入: [(query, doc1), (query, doc2), ...]
pairs = [(user_query, doc) for doc in retrieved_docs]
scores = reranker.predict(pairs)

# 按分数排序,取 top-3
ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
top3_indices = ranked_indices[:3]
print(f"分数排名:{top3_indices}")

print(f"\nRerank 精排: 取 top-3")
reranked_docs = []
reranked_meta = []
for rank, idx in enumerate(top3_indices):
    doc = retrieved_docs[idx]
    meta = retrieved_meta[idx]
    score = scores[idx]
    print(f"  #{rank + 1} 分数={score:.4f} [{meta['source']}] {doc[:60]}...")
    reranked_docs.append(doc)
    reranked_meta.append(meta)

# ---- 第 3 步: 拼进 prompt 让模型回答 ----
context = "\n\n".join([f"[{meta['source']}]\n{doc}" for doc, meta in zip(reranked_docs, reranked_meta)])
prompt = f"""你是一个助手,请根据以下参考资料回答用户问题。如果资料里没有相关信息,就说"参考资料里没有找到"。

## 参考资料
{context}

## 用户问题
{user_query}

## 你的回答"""

messages = [{"role": "user", "content": prompt}]
response = client.chat.completions.create(
    model=MODEL,
    messages=messages
)

answer = response.choices[0].message.content
print(f"\nAI 回答(基于 Rerank RAG):\n{answer}")
