"""阶段 3 的手写向量检索,包装成一个普通 @tool 工具。
对 Agent 来说 RAG 没有特殊地位:它就是菜单上又一道菜"""
import os

import llm_client
from tools import tool

# 知识库语料直接复用阶段 3 的 knowledge 目录,不复制一份
KNOWLEDGE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "03_rag", "knowledge"))
STORE_FILE = "vectors.json"
TOP_K = 4


# ========== 下面三个成员从 03_rag/04_rag_chat.py 原样照抄,一行没改 ==========
def cosine(vec_a, vec_b):
    """余弦相似度:点积 / (|a| * |b|),越接近 1 语义越近"""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    return dot / (norm_a * norm_b)


class SimpleVectorStore:
    """手写向量库:一个列表 + 线性扫描 + JSON 落盘"""

    def __init__(self):
        self.items = []   # 每个元素 {"text": ..., "source": ..., "vector": [...]}

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
        store = cls()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                store.items = json.load(f)
        return store


def chunk_by_size(text, size=400, overlap=50):
    """固定长度滑窗切块,overlap 是给被切断句子留的重叠带"""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


# ★ chunk_text 不照抄:知识库是 txt 段落式语料,没有 Markdown 标题可依。
#   原来的"按标题切"在这种语料上退化成"一个文件一大块"(实测 25 块变 5 块),
#   检索直接失灵——切块策略永远要顺着语料结构来:md 按标题,txt 按空行分段。
def chunk_text(text, max_len=500):
    """按空行分段(一段一个独立事实),超长段落再用滑窗细切"""
    chunks = []
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if len(para) <= max_len:
            chunks.append(para)
        else:
            chunks.extend(chunk_by_size(para, size=400, overlap=50))
    return chunks


# ========== 新写的胶水:建库 + 懒加载 + 工具化 ==========
def _build_store():
    """全量重建:读 knowledge 的文档 → 切块 → 向量化 → 落盘"""
    pending = []   # (块文本, 来源文件名)
    for name in sorted(os.listdir(KNOWLEDGE_DIR)):
        path = os.path.join(KNOWLEDGE_DIR, name)
        if os.path.isfile(path) and name.lower().endswith((".md", ".txt")):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            for chunk in chunk_text(text):
                pending.append((chunk, name))
    if not pending:
        raise SystemExit(f"知识库目录是空的:{KNOWLEDGE_DIR}")

    print(f"(共 {len(pending)} 块,开始向量化…)")
    vectors = llm_client.embed_texts([t for t, _ in pending])
    store = SimpleVectorStore()
    for (text, source), vec in zip(pending, vectors):
        store.add(text, vec, source)
    store.save(STORE_FILE)
    print(f"(知识库已建立:{len(pending)} 块 → {STORE_FILE})")
    return store


_store = None


def get_store():
    """懒加载单例:有缓存读缓存,没缓存才建库。慢资源第一次用时再建"""
    global _store
    if _store is None:
        _store = SimpleVectorStore.load(STORE_FILE)
        if not _store.items:
            _store = _build_store()
    return _store


@tool
def search_knowledge(query: str) -> str:
    """查询星链公司内部知识库(考勤假期、报销流程、IT与账号、研发规范、园区设施)。凡涉及公司内部规定的问题必须调用本工具,禁止凭已有知识回答。"""
    q_vec = llm_client.embed_texts([query])[0]
    hits = get_store().search(q_vec, TOP_K)
    if not hits:
        return "知识库里没有相关内容"

    # 带来源返回,模型回答可溯源(阶段 3 引用编号的思想)
    return "\n\n".join(f"[来源:{it['source']}] {it['text']}" for _, it in hits)
