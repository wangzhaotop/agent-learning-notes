"""第 7 课:结构化输出 + 校验失败重试的单测(0 token)"""
from types import SimpleNamespace

from pydantic import BaseModel

import structured


def fake_llm(content):
    """伪造 llm_client.chat 的返回(只需要 choices[0].message.content)"""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class Card(BaseModel):
    answer: str


def test_一次就合格(monkeypatch):
    monkeypatch.setattr(structured.llm_client, "chat",
                        lambda *a, **k: fake_llm('{"answer": "好的"}'))
    card, attempt = structured.ask_structured("hi", Card)
    assert card.answer == "好的"
    assert attempt == 0


def test_第一次不合格_打回重试(monkeypatch):
    outputs = iter(['{"answer": "好的"',             # 缺右括号,非法 JSON
                    '{"answer": "好的"}'])           # 重写后合格
    monkeypatch.setattr(structured.llm_client, "chat",
                        lambda *a, **k: fake_llm(next(outputs)))
    card, attempt = structured.ask_structured("hi", Card)
    assert card.answer == "好的"
    assert attempt == 1                              # 确实重试了一次


def test_一直不合格_返回None(monkeypatch):
    monkeypatch.setattr(structured.llm_client, "chat",
                        lambda *a, **k: fake_llm("我不是JSON"))
    card, attempt = structured.ask_structured("hi", Card, retries=1)
    assert card is None


def test_schema_塞进system_用户话是user角色(monkeypatch):
    seen = {}

    def spy(messages, **kwargs):
        seen["messages"] = messages
        return fake_llm('{"answer": "好的"}')

    monkeypatch.setattr(structured.llm_client, "chat", spy)
    structured.ask_structured("hi", Card)

    assert "JSON Schema" in seen["messages"][0]["content"]
    assert "'answer'" in seen["messages"][0]["content"]     # 字段说明自动生成并注入了
    assert seen["messages"][1]["role"] == "user"            # 用户的话不许写成 system


def test_真实Reply模型_字段齐全(monkeypatch):
    monkeypatch.setattr(
        structured.llm_client, "chat",
        lambda *a, **k: fake_llm('{"answer": "15 天", "intent": "kb", "need_search": true}'),
    )
    obj, attempt = structured.ask_structured("年假能攒多少天", structured.Reply)
    assert (obj.intent, obj.need_search, attempt) == ("kb", True, 0)
