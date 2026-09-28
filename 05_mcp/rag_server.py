"""05_mcp/rag_server.py —— 阶段 3 的检索,发布成一个 MCP server"""
import os
import sys

from mcp.server.mcpserver import MCPServer

import llm_client

KNOWLEDGE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "03_rag", "knowledge")
)
STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors.json")
TOP_K = 4

server = MCPServer(name="knowledge-server", version="0.1.0", instructions="星链公司内部知识库")


def cosine(vec_a, vec_b):
    """余弦相似度:点积 / (|a| * |b|)"""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    return dot / (norm_a * norm_b)


class SimpleVectorStore:
    """手写一个向量库: 一个列表 + 线性扫描 + JSON 落盘"""

    def __init__(self):
        self.items = []

    def add(self, text, vector, source=""):
        self.items.append({"text": text, "source": source, "vector": vector})

    def search(self, query_vector, top_k):
        scored = [(cosine(query_vector, it["vector"]), it) for it in self.items]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[:top_k]

    def save(self, path):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False)

    @classmethod
    def load(cls, path):
        import json
        # 实例化一个
        store = cls()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                store.items = json.load(f)
        return store


def chunk_by_size(text, size=400, overlap=50):
    """固定长度滑窗切块"""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def chunk_text(text, max_len=500):
    chunks = []
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if len(para) <= max_len:
            chunks.append(para)
        else:
            chunks.extend(chunk_by_size(para))

    return chunks


# ===== 服务端专属:建库 + 懒加载 + 暴露成 MCP 工具 =====
def _build_store():
    pending = []
    for name in sorted(os.listdir(KNOWLEDGE_DIR)):
        path = os.path.join(KNOWLEDGE_DIR, name)
        if os.path.isfile(path) and name.lower().endswith((".md", ".txt")):
        # ★ endswith 只收一个参数,多个后缀要打包成元组;
        #   写成 endswith(".md", ".txt") 时 ".txt" 会被当成切片起始位置 → TypeError
            with open(path, "r", encoding="utf-8") as f:
                for chunk in chunk_text(f.read()):
                    pending.append((chunk, name))
    if not pending:
        raise SystemExit(f"知识库目录是空的:{KNOWLEDGE_DIR}")

    vectors = llm_client.embed_text([t for t, _ in pending])
    store = SimpleVectorStore()
    for (text, source), vector in zip(pending, vectors):
        store.add(text, vector, source)
    store.save(STORE_FILE)
    print(f"(知识库已建立:{len(pending)} 块)", file=sys.stderr)  # ★ 日志走 stderr
    return store


_store = None


def get_store():
    """懒加载单例:有缓存读缓存,没缓存才建库"""
    global _store
    if _store is None:
        _store = SimpleVectorStore.load(STORE_FILE)
        if not _store.items:
            _store = _build_store()
    return _store


@server.tool()
def search_knowledge(query: str) -> str:
    """查询星链公司内部知识库(考勤假期、报销流程、IT与账号、研发规范、园区设施)。凡涉及公司内部规定的问题必须调用本工具。"""
    q_vec = llm_client.embed_text([query])[0]
    hits = get_store().search(q_vec, TOP_K)
    if not hits:
        return "知识库中没有这个内容"
    return "\n\n".join(f"[来源:{it['source']}] {it['text']}" for _, it in hits)

if __name__ == "__main__":
    server.run()
