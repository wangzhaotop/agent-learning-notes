"""第 7 课:RAG 工具的单测——embedding 也要 mock,单测一分钱不花"""
import rag


def test_按空行分段_每段独立事实():
    text = "第一段事实。\n\n第二段事实。\n\n\n第三段事实。"
    assert len(rag.chunk_text(text)) == 3


def test_超长段落_再用滑窗细切():
    chunks = rag.chunk_text("啊" * 1200)
    assert len(chunks) > 1
    assert all(len(c) <= 400 for c in chunks)


def test_命中_返回带来源(monkeypatch):
    monkeypatch.setattr(rag.llm_client, "embed_texts", lambda texts: [[1.0, 0.0]])
    store = rag.SimpleVectorStore()
    store.add("年假最多能攒 15 天。", [1.0, 0.0], "考勤与假期.txt")
    monkeypatch.setattr(rag, "get_store", lambda: store)

    out = rag.search_knowledge("年假能攒多少天")
    assert "[来源:考勤与假期.txt]" in out
    assert "年假最多能攒 15 天。" in out


def test_没有命中_返回兜底(monkeypatch):
    monkeypatch.setattr(rag.llm_client, "embed_texts", lambda texts: [[1.0, 0.0]])
    monkeypatch.setattr(rag, "get_store", lambda: rag.SimpleVectorStore())
    assert rag.search_knowledge("随便问问") == "知识库里没有相关内容"


def test_相似度排序_越近越靠前(monkeypatch):
    monkeypatch.setattr(rag.llm_client, "embed_texts", lambda texts: [[1.0, 0.0]])
    store = rag.SimpleVectorStore()
    store.add("远", [0.0, 1.0], "far.txt")
    store.add("近", [1.0, 0.0], "near.txt")
    monkeypatch.setattr(rag, "get_store", lambda: store)

    out = rag.search_knowledge("近的那条")
    assert out.index("near.txt") < out.index("far.txt")
