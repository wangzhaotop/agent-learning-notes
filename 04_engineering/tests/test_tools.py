"""第 7 课:注册器 + 统一执行出口的单测(0 token)"""
from tools import TOOL_REGISTRY, call_tool, get_openai_tools


def test_每个工具都有说明书():
    for name, meta in TOOL_REGISTRY.items():
        assert meta["doc"], f"工具 {name} 缺 docstring——模型看不见它的用途"


def test_schema_按注解自动生成():
    schema = TOOL_REGISTRY["write_file"]["params"]
    assert schema["properties"]["path"]["type"] == "string"
    assert schema["properties"]["content"]["type"] == "string"
    assert set(schema["required"]) == {"path", "content"}


def test_openai_tools_符合协议格式():
    tools = get_openai_tools()
    assert tools, "注册表是空的"
    assert all(t["type"] == "function" for t in tools)
    assert "get_current_time" in {t["function"]["name"] for t in tools}


def test_调用不存在的工具_兜底():
    assert "不存在" in call_tool("no_such_tool", {})


def test_执行出错_兜底成字符串(tmp_path):
    result = call_tool("read_file", {"path": str(tmp_path / "不存在.txt")})
    assert "工具执行出错" in result
